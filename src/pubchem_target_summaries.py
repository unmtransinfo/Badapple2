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
    # see https://www.uniprot.org/help/accession_number
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
        target_info = assay.target
        # default format has target accession under 'mol_id' - fixing this
        if target_info is not None:
            protein_targets = list(filter(has_protein_accession, target_info))
            for target_details in protein_targets:
                protein_accession = target_details["mol_id"]["protein_accession"]
                target_details["protein_accession"] = protein_accession
                del target_details["mol_id"]
                if args.fetch_uniprot_ids:
                    target_details["uniprot_id"] = get_uniprot_id(protein_accession)
            if len(protein_targets) != len(target_info):
                print(f"Non protein target for AID {aid}")
        aid2target[aid] = target_info

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
