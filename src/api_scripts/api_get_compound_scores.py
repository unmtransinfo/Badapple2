"""
@author Jack Ringer
Date: 9/25/2024
Description:
Get the promiscuity scores for compounds from a given TSV file. Uses
Badapple2-API: https://github.com/unmtransinfo/Badapple2-API
"""

import argparse
import json

import pandas as pd
import requests
from tqdm import tqdm


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--input_tsv",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="input compounds (TSV file). Expects compound SMILES to be in a column with header 'SMILES'",
    )
    parser.add_argument(
        "--output_tsv",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="output file, will include all info from input TSV + two new columns: molecule pscore and corresponding scaffold",
    )
    return parser.parse_args()


def main(args):
    API_URL = "http://localhost:8000/api/v1/compound_search/get_high_scores"
    cpd_df = pd.read_csv(args.input_tsv, sep="\t")
    smiles_list = cpd_df["SMILES"].tolist()
    scaffold_smiles = []
    scaffold_indrug = []
    scaffold_ids = []
    pscores = []
    for smiles in tqdm(smiles_list, "Processing SMILES..."):
        response = requests.get(
            API_URL,
            params={"SMILES": smiles},
        )
        data = json.loads(response.text)[0]
        scaffold_info = data["highest_scoring_scaf"]
        scaffold_smiles.append(scaffold_info.get("scafsmi"))
        scaffold_indrug.append(scaffold_info.get("in_drug"))
        scaffold_ids.append(scaffold_info.get("id"))
        pscores.append(scaffold_info.get("pscore"))
    cpd_df["pscore"] = pscores
    cpd_df["scafsmi"] = scaffold_smiles
    cpd_df["in_drug"] = scaffold_indrug
    cpd_df["scafid"] = scaffold_ids
    cpd_df.to_csv(args.output_tsv, sep="\t", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get pscores for input SMILES from a TSV file. For each compound, the corresponding pscore is from scaffold which had the highest pscore (this scaffold's SMILES included in output).",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
