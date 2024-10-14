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
    parser.add_argument(
        "--include_all_scaffolds",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Report all scaffolds/scores for each input molecule. If False will only report highest-scoring scaffold.",
    )
    return parser.parse_args()


def main(args):
    # TODO: update from localhost to actual website once API deployed
    if args.include_all_scaffolds:
        API_URL = (
            "http://localhost:8000/api/v1/compound_search/get_associated_scaffolds"
        )
    else:
        API_URL = "http://localhost:8000/api/v1/compound_search/get_high_scores"

    cpd_df = pd.read_csv(args.input_tsv, sep="\t")

    with open(args.output_tsv, "w") as output_file:
        original_header = cpd_df.columns.tolist()
        new_columns = ["scafsmi", "in_drug", "id", "pscore"]
        output_file.write("\t".join(original_header + new_columns) + "\n")

        for _, row in tqdm(
            cpd_df.iterrows(), desc="Processing rows...", total=cpd_df.shape[0]
        ):
            smiles = row["SMILES"]
            response = requests.get(API_URL, params={"SMILES": smiles})
            data = json.loads(response.text)
            if data is None:
                print(f"Invalid SMILES given: {smiles}, skipping to next row...")
                continue
            if args.include_all_scaffolds:
                data = data[smiles]
            else:
                data = [data[0]["highest_scoring_scaf"]]

            original_row = row.tolist()
            for scaffold_info in data:
                scaffold_smiles = scaffold_info.get("scafsmi")
                scaffold_indrug = scaffold_info.get("in_drug")
                scaffold_id = scaffold_info.get("id")
                pscore = scaffold_info.get("pscore")

                output_file.write(
                    "\t".join(
                        map(
                            str,
                            original_row
                            + [scaffold_smiles, scaffold_indrug, scaffold_id, pscore],
                        )
                    )
                    + "\n"
                )
            if len(data) == 0:
                # include row w/ none
                output_file.write(
                    "\t".join(
                        map(
                            str,
                            original_row + [None, None, None, None],
                        )
                    )
                    + "\n"
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get pscores for input SMILES from a TSV file. For each compound, the corresponding pscore is from scaffold which had the highest pscore (this scaffold's SMILES included in output).",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
