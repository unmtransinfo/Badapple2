"""
@author Jack Ringer
Date: 7/1/2024
Description:
Script to download assay data from PubChem using the PUG REST API:
https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest-tutorial#section=Access-to-PubChem-BioAssays 
"""

import argparse
import io
import os
import time

import pandas as pd
import requests
from tqdm import tqdm


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--aid_file",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="text file containing assays ids (one id/line)",
    )
    parser.add_argument(
        "--out_dir",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="directory to save assay summaries to. files saved with format <aid>.csv",
    )
    return parser.parse_args()


def read_aid_file(aid_file_path: str) -> list[int]:
    with open(aid_file_path, "r") as file:
        aid_list = [int(line.strip()) for line in file if line.strip().isdigit()]
    return aid_list


def fetch_csv_summary(aid: int) -> pd.DataFrame:
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/%d/concise/CSV" % aid
    response = requests.get(url)
    if response.status_code == 200:
        data = response.content.decode("utf-8")
        df = pd.read_csv(io.StringIO(data))
    else:
        print(
            f"Failed to retrieve data for aid {aid}. Status code: {response.status_code}"
        )
        df = None
    return df


def main(args):
    os.makedirs(args.out_dir, exist_ok=True)
    assay_ids = read_aid_file(args.aid_file)
    start = time.time()
    for aid in tqdm(assay_ids):
        aid_df = fetch_csv_summary(aid)
        if aid_df is not None:
            save_path = os.path.join(args.out_dir, f"{aid}.csv")
            aid_df.to_csv(save_path)
    end = time.time()
    print("Time elapsed:", end - start)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch assay info using assay id (AID) file", epilog=""
    )
    args = parse_args(parser)
    main(args)
