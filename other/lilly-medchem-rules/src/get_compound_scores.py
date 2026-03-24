"""
@author Jack Ringer
Date: 4/30/2025
Description:
Get the promiscuity scores for all scaffolds for compounds from a given TSV file using API.
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
        "--input_dsv_file",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="Delimiter-separated file (e.g., CSV) which contains molecule names and SMILES",
    )
    parser.add_argument(
        "--idelim",
        type=str,
        default="\t",
        help="Delimiter for input DSV file (default is tab)",
    )
    parser.add_argument(
        "--iheader",
        action="store_true",
        help="Input DSV file has header line",
    )
    parser.add_argument(
        "--smiles_column",
        type=int,
        default=0,
        help="(integer) column where SMILES are located (for input DSV file)",
    )
    parser.add_argument(
        "--name_column",
        type=int,
        default=1,
        help="(integer) column where molecule names are located (for input DSV file). Names should be unique!",
    )
    parser.add_argument(
        "--output_tsv",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="Output TSV file, will include all info from input DSV as well as Badapple info (scafID, pScore, inDrug, etc)",
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
    parser.add_argument(
        "--database",
        type=str,
        required=False,
        default="badapple_classic",
        help="Badapple database to fetch info from",
    )
    parser.add_argument(
        "--local_port",
        type=int,
        required=False,
        default=0,
        help="(Localhost only) API port. Provide only if you have setup and would like to use the local version of Badapple2-API.",
    )
    return parser.parse_args()


def read_df(fpath: str, delim: str, header: bool) -> pd.DataFrame:
    if header:
        df = pd.read_csv(fpath, sep=delim)
    else:
        df = pd.read_csv(fpath, sep=delim, header=None)
    return df


def main(args):
    batch_size = args.batch_size
    using_localhost = args.local_port > 0
    max_batch_size = 1000
    if batch_size < 0 or batch_size > max_batch_size:
        raise ValueError(
            f"Batch size must be within [1,{max_batch_size}]. Given: {batch_size}"
        )

    BASE_URL = ""
    if using_localhost:
        BASE_URL = f"http://localhost:{args.local_port}/api/v1"
    else:
        BASE_URL = "https://chiltepin.health.unm.edu/badapple2/api/v1"
    API_URL = f"{BASE_URL}/compound_search/get_associated_scaffolds_ordered"
    cpd_df = read_df(args.input_dsv_file, args.idelim, args.iheader)
    smiles_col_name = cpd_df.columns[args.smiles_column]
    names_col_name = cpd_df.columns[args.name_column]

    n_compound_total = len(cpd_df)
    if n_compound_total > 10_000 and not (using_localhost):
        raise ValueError(
            f"Input file had {n_compound_total} > 10,000 compounds. If processing this many compounds please use locally-installed version (it will be much faster)! See: https://github.com/unmtransinfo/Badapple2-API?tab=readme-ov-file#setup-local-installation"
        )
    batches = np.arange(n_compound_total) // batch_size
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
        for batch_num, sub_df in tqdm(cpd_df.groupby(batches)):
            smiles_list = sub_df[smiles_col_name].tolist()
            names_list = sub_df[names_col_name].tolist()
            response = requests.post(
                API_URL,
                json={
                    "SMILES": smiles_list,
                    "Names": names_list,
                    "max_rings": args.max_rings,
                    "database": args.database,
                },
            )
            if response.status_code != 200:
                raise ValueError(
                    f"Received bad response from API (you may need to lower batch_size):\n{response}\n{response.text}"
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
        description="Get scaffold pScores and other info for input compound SMILES from a TSV file.",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
