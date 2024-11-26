"""
@author Jack Ringer
Date: 9/25/2024
Description:
Get the promiscuity scores for all scaffolds for compounds from a given TSV file. Uses
Badapple2-API: https://github.com/unmtransinfo/Badapple2-API
"""

import argparse
import csv
import json

import numpy as np
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
        "--idelim",
        type=str,
        default="\t",
        help="delim for input SMI/TSV file (default is tab)",
    )
    parser.add_argument(
        "--iheader",
        action="store_true",
        help="input SMILES/TSV has header line",
    )
    parser.add_argument(
        "--smiles_column",
        type=int,
        default=0,
        help="(integer) column where SMILES are located (for input SMI file)",
    )
    parser.add_argument(
        "--name_column",
        type=int,
        default=1,
        help="(integer) column where molecule names are located (for input SMI file). Names should be unique!",
    )
    parser.add_argument(
        "--max_rings",
        type=int,
        required=False,
        default=5,
        help="Maximum number of ring systems allowed in input compounds. Compounds with > max_rings will not be processed. Note that the API will hard cap you at 10.",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        required=False,
        default=100,
        help="Number of compounds to fetch scaffold details on with each request. Note that the API will hard cap you at 1000, recommended to be <=100",
    )
    return parser.parse_args()


def main(args):
    batch_size = args.batch_size
    if batch_size <= 0 or batch_size > 100:
        raise ValueError(f"Batch size must be within [1,100]. Given: {batch_size}")

    API_URL = "https://chiltepin.health.unm.edu/badapple2/api/v1/compound_search/get_associated_scaffolds_ordered"
    cpd_df = None
    if args.iheader:
        cpd_df = pd.read_csv(args.input_tsv, sep=args.idelim)
    else:
        cpd_df = pd.read_csv(args.input_tsv, sep=args.idelim, header=None)
    smiles_col_name = cpd_df.columns[args.smiles_column]
    names_col_name = cpd_df.columns[args.name_column]
    if cpd_df[smiles_col_name].isna().any():
        raise ValueError(
            "SMILES column cannot contain blank (None) entries, please check input"
        )
    if cpd_df[names_col_name].isna().any():
        raise ValueError(
            "Name column cannot contain blank (None) entries, please check input"
        )
    n_compound_total = len(cpd_df)
    batches = np.arange(n_compound_total) // batch_size
    total_batches = (n_compound_total // batch_size) + 1
    with open(args.output_tsv, "w") as output_file:
        out_writer = csv.writer(output_file, delimiter="\t")
        out_header = [
            "molIdx",
            "molSmiles",
            "molName",
            "validMol",
            "scafSmiles",
            "inDB",
            "scafID",
            "pScore",
            "inDrug",
            "substancesTested",
            "substancesActive",
            "assaysTested",
            "assaysActive",
            "samplesTested",
            "samplesActive",
        ]
        if args.iheader:
            out_header[2] = names_col_name

        out_writer.writerow(out_header)
        molIdx = 0
        for batch_num, sub_df in tqdm(
            cpd_df.groupby(batches),
            desc="Processing batches of compounds",
            total=total_batches,
        ):
            smiles_list = ",".join(sub_df[smiles_col_name].tolist())
            names_list = ",".join(sub_df[names_col_name].tolist())
            response = requests.get(
                API_URL,
                params={
                    "SMILES": smiles_list,
                    "Names": names_list,
                    "max_rings": args.max_rings,
                },
            )
            # data will be list of dictionaries, 1 for each mol in batch
            data = json.loads(response.text)
            rows = []
            for badapple_dict in data:
                scaffold_infos = badapple_dict.get("scaffolds", None)
                valid_mol = (
                    scaffold_infos is not None
                )  # scaf_list will be [] if valid mol with no scafs
                if valid_mol and len(scaffold_infos) > 0:
                    for d in scaffold_infos:
                        row = [
                            molIdx,
                            badapple_dict["molecule_smiles"],
                            badapple_dict["name"],
                            valid_mol,
                            d["scafsmi"],
                            d["in_db"],
                            d.get("id", None),  # None if not(in_db)
                            d.get("pscore", None),
                            d.get("in_drug", None),
                            d.get("nsub_tested", None),
                            d.get("nsub_active", None),
                            d.get("nass_tested", None),
                            d.get("nass_active", None),
                            d.get("nsam_tested", None),
                            d.get("nsam_active", None),
                        ]
                        rows.append(row)
                else:
                    row = [
                        molIdx,
                        badapple_dict["molecule_smiles"],
                        badapple_dict["name"],
                        valid_mol,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                    ]
                    rows.append(row)
                molIdx += 1
            out_writer.writerows(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get scaffold pscores for input compound SMILES from a TSV file.",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
