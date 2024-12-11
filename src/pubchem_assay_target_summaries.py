"""
@author Jack Ringer
Date: 9/9/2024
Description:
Get info on targets for a given list of PubChem assay ids (AIDs).
The input file is expected to only contain a list of AIDs, with each id
separated by a newline.
"""

import argparse
import json
import os
from typing import Tuple

import pubchempy as pcp
import requests
from tqdm import tqdm

from utils.file_utils import read_aid_file
from utils.target_utils import TargetType, is_valid_uniprot_id, strip_version


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--aid_file",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="input text file containing assays ids (one id/line)",
    )
    parser.add_argument(
        "--out_json_file",
        type=str,
        default="aid2target.json",
        help="JSON output file mapping AID to list of targets",
    )
    parser.add_argument(
        "--fetch_uniprot_ids",
        action=argparse.BooleanOptionalAction,
        help="For each protein target, determine the UniProt id (if possible)",
    )
    return parser.parse_args()


def get_target_type_and_id(item: dict) -> Tuple[str, str]:
    if "mol_id" in item:
        id_info = item["mol_id"]
        if "protein_accession" in id_info:
            return TargetType.PROTEIN.value, id_info["protein_accession"]
        if "nucleotide_accession" in id_info:
            return TargetType.NUCLEOTIDE.value, id_info["nucleotide_accession"]
        elif "gene_id" in id_info:
            return TargetType.GENE.value, id_info["gene_id"]
        elif "other" in id_info and id_info["other"].startswith("Pathway"):
            return TargetType.PATHWAY.value, id_info["other"]
        raise ValueError(f"Unrecognized target type in item: {item}")
    return None, None


def extract_uniprot_id(json_data: dict):
    if (
        "ProteinSummaries" in json_data
        and "ProteinSummary" in json_data["ProteinSummaries"]
    ):
        # summary page will prioritize uniprot id, but if not available will give other id
        uniprot_candidate = json_data["ProteinSummaries"]["ProteinSummary"][0][
            "ProteinAccession"
        ]
        if is_valid_uniprot_id(uniprot_candidate):
            return uniprot_candidate
    return None


def get_uniprot_id(protein_accession: str) -> str:
    pure_accession = strip_version(protein_accession)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/synonym/{pure_accession}/summary/JSON"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        uniprot_id = extract_uniprot_id(data)
        return uniprot_id
    print(f"Failed to retrieve data for protein {protein_accession}")
    return None


def get_target_name(target_info: dict):
    possible_name_keys = ["name", "Name", "descr"]
    name = ""
    for name_key in possible_name_keys:
        name_candidate = target_info.get(name_key, "")
        if name_candidate != "":
            name = name_candidate
            break
    return name


def get_target_taxonomy(target_info: dict):
    organism_taxname = target_info.get("organism", {}).get("org", {}).get("taxname", "")
    return organism_taxname


def get_target_taxonomy_id(target_info: dict):
    db_entry = target_info.get("organism", {}).get("org", {}).get("db", [None])[0]
    taxon_id = ""
    if db_entry is not None:
        taxon_id = db_entry.get("tag", {}).get("id", "")
    return taxon_id


def fill_summary(summary: dict, target_info: dict):
    summary["Name"] = get_target_name(target_info)
    summary["Taxonomy"] = get_target_taxonomy(target_info)
    summary["TaxonomyID"] = get_target_taxonomy_id(target_info)


def get_target_summary(target_info: dict):
    summary = {}
    target_type, target_id = get_target_type_and_id(target_info)
    summary["TargetType"] = target_type
    summary["NCBI_ID"] = target_id
    # use information present in existing dict to try and fill in information
    fill_summary(summary, target_info)
    return summary


def main(args):
    if not (args.out_json_file.endswith(".json")):
        raise ValueError(
            f"out_json_file must have JSON filetype, please check arguments. Given filename was: {args.out_json_file}"
        )
    assay_ids = read_aid_file(args.aid_file)

    # get target info for each assay
    aid2target = {}
    for aid in tqdm(assay_ids, desc="Processing list of assay ids..."):
        assay = pcp.Assay.from_aid(aid)
        target_infos = assay.target
        target_summaries = []
        if target_infos is not None:
            for target_info in target_infos:
                target_summary = get_target_summary(target_info)
                if (
                    target_summary["TargetType"] == TargetType.PROTEIN.value
                    and args.fetch_uniprot_ids
                ):
                    target_summary["UniProtID"] = get_uniprot_id(
                        target_summary["NCBI_ID"]
                    )
                target_summaries.append(target_summary)
        aid2target[aid] = target_summaries

    # save output to JSON file
    out_dir = os.path.dirname(args.out_json_file)
    if out_dir != "":
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out_json_file, "w") as f:
        json.dump(aid2target, f, sort_keys=True, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get info on targets for a given list of PubChem assay ids",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
