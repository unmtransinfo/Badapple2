"""
@author Jack Ringer
Date: 11/14/2024
Description:
Script to gather protein family information from external sources.
"""

import argparse
from typing import Tuple

import pandas as pd
import requests
from tqdm import tqdm


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "inp_path",
        type=str,
        help="Path to input targets TSV file (output of json_to_tsv.py).",
    )
    parser.add_argument(
        "out_path",
        type=str,
        help="Path to output TSV file with updated protein family information.",
    )
    args = parser.parse_args()
    return args


def _get_family_pharos(uniprot_id: str):
    # get the protein family from pharos using GraphQL api
    api_url = "https://pharos-api.ncats.io/graphql"
    query_str = f"""
        query targetDetails {{
        target(q: {{uniprot: "{uniprot_id}"}}) {{
            fam
        }}
        }}
        """
    response = requests.post(api_url, json={"query": query_str})
    family = None
    if response.status_code == 200:
        data = response.json()
        if data["data"]["target"] is not None:
            family = data["data"]["target"]["fam"]
    else:
        print(f"Failed to get family for: {uniprot_id}")
    return family


def get_protein_family(uniprot_id: str) -> Tuple[str, str]:
    family = _get_family_pharos(uniprot_id)
    datasource = None
    if family is None:
        pass  # in future may want to add other datasources
    else:
        datasource = "Pharos"
    return family, datasource


def main(args):
    df = pd.read_csv(args.inp_path, sep="\t")
    families = []
    data_sources = []
    for _, row in tqdm(df.iterrows(), "Getting protein families", total=len(df)):
        if row["TargetType"] == "Protein" and pd.notna(row["UniProtID"]):
            family, data_source = get_protein_family(row["UniProtID"])
            families.append(family)
            data_sources.append(data_source)
        else:
            families.append(None)
            data_sources.append(None)

    df["ProteinFamily"] = families
    df["FamilyDataSource"] = data_sources
    df.to_csv(args.out_path, sep="\t", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gather protein family information from external sources. Only gathers family info for proteins with UniProtID."
    )
    args = parse_args(parser)
    main(args)
