"""
@author Jack Ringer
Date: 11/20/2024
Description:
For a given target TSV file, fill in information (Name, Taxonomy, etc) using
the PubChem API. Will also overwrite NCBI_ID with UniProtID for protein targets
for the sake of consistency.

The reason this is done on top of pubchem_assay_target_summaries.py
is for the following reasons:
1) To allow for (in theory) adding in additional targets in other parts of the workflow
2) To ensure consistency (target info from assay records does not always exactly match with the PubChem protein/gene DBs)
"""

import argparse
import json

import pandas as pd
import requests
from tqdm import tqdm

from utils.target_utils import TargetType


def fetch_target_summary(target_row: dict):
    # if target type is gene or protein can use PubChem API to fill in name + taxonomy info
    # otherwise have to rely on what is present in target_row
    url = None
    target_id = target_row["NCBI_ID"]
    target_type = target_row["TargetType"]
    if target_type not in [TargetType.PROTEIN.value, TargetType.GENE.value]:
        return None
    elif target_type == TargetType.PROTEIN.value:
        if not (pd.isna(target_row["UniProtID"])):
            # prefer UniProtID over NCBI_ID
            target_id = target_row["UniProtID"]
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/protein/accession/{target_id}/summary/JSON"
    else:
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/gene/geneid/{target_id}/summary/JSON"

    # use PubChemAPI to get information (more consistent than raw data from assays)
    fetched_summary = None
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        data_summary = data[f"{target_type}Summaries"][f"{target_type}Summary"][0]
        fetched_summary = {}
        fetched_summary["Name"] = data_summary["Name"]
        fetched_summary["Taxonomy"] = data_summary["Taxonomy"]
        fetched_summary["TaxonomyID"] = data_summary["TaxonomyID"]
    else:
        print(f"Failed to fetch summary for gene/protein: {target_id}")
    return fetched_summary


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--input_tsv",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="Input targets TSV file",
    )
    parser.add_argument(
        "--out_tsv",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="Output/cleaned targets TSV file",
    )
    return parser.parse_args()


def main(args):
    df = pd.read_csv(args.input_tsv, sep="\t")
    for i, row in tqdm(df.iterrows(), "Fetching target summaries", total=len(df)):
        summary = fetch_target_summary(row)
        if summary is not None:
            for key in summary:
                df.at[i, key] = summary[key]
    df.to_csv(args.out_tsv, sep="\t", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Use PubChem API to improve the consistency of entry information for proteins and genes",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
