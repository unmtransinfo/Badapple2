"""
@author Jack Ringer
Date: 11/20/2024
Description:
Create the "target" table to be used in the Badapple2 DB.
"""

import argparse

import pandas as pd

from utils.target_utils import TargetType


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--inp_tsv",
        type=str,
        help="Path to input targets TSV file",
    )
    parser.add_argument(
        "--out_tsv",
        type=str,
        help="Path to output TSV (final target table)",
    )
    args = parser.parse_args()
    return args


def main(args):
    column_map = {
        "TargetID": "target_id",
        "TargetType": "type",
        "Name": "name",
        "Taxonomy": "taxonomy",
        "TaxonomyID": "taxonomy_id",
        "ProteinFamily": "protein_family",
    }
    column_order = [
        "target_id",
        "type",
        "external_id",
        "external_id_type",
        "name",
        "taxonomy",
        "taxonomy_id",
        "protein_family",
    ]
    df = pd.read_csv(args.inp_tsv, sep="\t")
    df["external_id"] = df["NCBI_ID"]
    df["external_id_type"] = "NCBI"

    # prefer UniProtID over NCBI id
    uniprot_index = df.index[~df["UniProtID"].isna()]
    df.loc[uniprot_index, "external_id"] = df.loc[uniprot_index, "UniProtID"]
    df.loc[uniprot_index, "external_id_type"] = "UniProt"

    # pathway ids come from outside NCBI
    pathway_index = df.index[df["TargetType"] == TargetType.PATHWAY.value]
    df.loc[pathway_index, "external_id_type"] = "Other"

    # rename and arrange columns and save
    df.rename(columns=column_map, inplace=True)
    df = df[column_order]
    df.to_csv(args.out_tsv, sep="\t", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create the 'target' table to be used in the Badapple2 DB"
    )
    args = parse_args(parser)
    main(args)
