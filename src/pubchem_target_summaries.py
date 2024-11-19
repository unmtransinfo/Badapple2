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
import re
from typing import Tuple

import pubchempy as pcp
import requests
from tqdm import tqdm

from utils.file_utils import read_aid_file


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
            return "Protein", id_info["protein_accession"]
        if "nucleotide_accession" in id_info:
            return "Nucleotide", id_info["nucleotide_accession"]
        elif "gene_id" in id_info:
            return "Gene", id_info["gene_id"]
        elif "other" in id_info and id_info["other"].startswith("Pathway"):
            return "Pathway", id_info["other"]
        raise ValueError(f"Unrecognized target type in item: {item}")
    return None, None


def strip_version(protein_accession: str):
    # some accession strings include version at the end
    # e.g., "NP_004408.1" indicates version 1 (".1")
    # remove these versions so the accession can be used w/ PubChem API
    pos = protein_accession.rfind(".")
    if pos != -1:
        return protein_accession[:pos]
    return protein_accession


UNIPROT_REGEX = r"[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}"


def is_valid_uniprot_id(uniprot_candidate: str):
    # see https://www.uniprot.org/help/accession_numbers
    return re.match(UNIPROT_REGEX, uniprot_candidate)


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
    url = None
    summary = {}
    target_type, target_id = get_target_type_and_id(target_info)
    summary["TargetType"] = target_type
    summary["PubChemID"] = target_id
    filled_summary = False

    # if target type is gene or protein can use PubChem API to fill in name + taxonomy info
    # otherwise have to rely on what's present in target_info
    if target_type == "Protein":
        pure_accession = strip_version(target_id)
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/{pure_accession}/summary/JSON"
    elif target_type == "Gene":
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/{target_id}/summary/JSON"
    if url is not None:
        # use PubChemAPI to get information (more consistent than raw data from assays)
        response = requests.get(url)
        if response.status_code == 200:
            data = json.loads(response.text)
            data_summary = data[f"{target_type}Summaries"][f"{target_type}Summary"][0]
            summary["Name"] = data_summary["Name"]
            summary["Taxonomy"] = data_summary["Taxonomy"]
            summary["TaxonomyID"] = data_summary["TaxonomyID"]
            filled_summary = True
        else:
            print(f"Failed to fetch summary for gene/protein: {target_id}")
    if not (filled_summary):
        # use information present in existing dict to try and fill in information
        fill_summary(summary, target_info)
    return summary


def has_protein_accession(target_details: dict):
    return (
        "mol_id" in target_details and "protein_accession" in target_details["mol_id"]
    )


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
                if target_summary["TargetType"] == "Protein" and args.fetch_uniprot_ids:
                    target_summary["UniProtID"] = get_uniprot_id(
                        target_summary["PubChemID"]
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
