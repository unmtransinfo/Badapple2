"""
@author Jack Ringer
Date: 7/22/2024
Description:
Script to load assay data from local files.
These local files were mirrored from PubChem bioassays (https://ftp.ncbi.nlm.nih.gov/pubchem/Bioassay/CSV/Data/)
via rsync (see sh_scripts/mirror_pubchem.sh).
"""

import argparse
import csv
import gzip
import os
import time
import zipfile

import pandas as pd


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--aid_file",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="text file containing assays ids (one id/line)",
    )
    parser.add_argument(
        "--zip_dir",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="path to directory containing assay .zip files",
    )
    return parser.parse_args()


def read_aid_file(aid_file_path: str) -> list[int]:
    with open(aid_file_path, "r") as file:
        aid_list = [int(line.strip()) for line in file if line.strip().isdigit()]
    return aid_list


def get_zip_filename(aid: int, file_per_zip: int = 1000, num_fill: int = 7) -> str:
    # <aid>.csv will be contained in file w/ name: <lower>_<upper>.zip
    # where lower <= aid <= upper
    # assuming each .zip contains the same number of files, starting with aid 1
    first_aid = 1
    lower_idx = (aid - first_aid) // file_per_zip
    upper_idx = (aid + file_per_zip - first_aid) // file_per_zip
    lower = (lower_idx * file_per_zip) + first_aid
    upper = upper_idx * file_per_zip
    lower = str(lower).zfill(num_fill)
    upper = str(upper).zfill(num_fill)
    return f"{lower}_{upper}.zip"


def find_data_start_row(file) -> int:
    with gzip.open(file, "rt") as decompressed_file:  # Decompress the file
        reader = csv.reader(decompressed_file)
        for i, row in enumerate(reader):
            try:
                if int(row[0]) > 0:
                    return i
            except ValueError:
                continue
    return None


def read_csv_files(
    zip_filepath: str, assay_ids: list[int], col_types: dict
) -> list[pd.DataFrame]:
    zip_filename = os.path.splitext(os.path.basename(zip_filepath))[0]
    dfs = []
    cols = list(col_types.keys())
    with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
        for aid in assay_ids:
            csv_filename = f"{zip_filename}/{aid}.csv.gz"
            with zip_ref.open(csv_filename, "r") as file:
                # pubchem csv files have a variable number of metadata headers
                start_row = find_data_start_row(file)
                # reopen since find_data_start_row consumes the file
                with zip_ref.open(csv_filename, "r") as file:
                    df = pd.read_csv(
                        file,
                        compression="gzip",
                        skiprows=range(1, start_row),
                        delimiter=",",
                        header=0,
                        usecols=cols,
                        dtype=col_types,
                    )
                    dfs.append(df)
    return dfs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Show assay info using assay id (AID) file", epilog=""
    )
    args = parse_args(parser)
    assay_ids = read_aid_file(args.aid_file)
    COL_TYPES = {
        "PUBCHEM_SID": "Int64",
        "PUBCHEM_CID": "Int64",
        "PUBCHEM_EXT_DATASOURCE_SMILES": str,
        "PUBCHEM_ACTIVITY_OUTCOME": str,
    }
    start = time.time()
    zip2aids = {}
    for aid in assay_ids:
        zip_filename = get_zip_filename(aid)
        zip2aids[zip_filename] = zip2aids.get(zip_filename, []) + [aid]

    for zip_filename, assay_ids in zip2aids.items():
        zip_filepath = os.path.join(args.zip_dir, zip_filename)
        assay_dfs = read_csv_files(zip_filepath, assay_ids, COL_TYPES)
        for assay_id, df in zip(assay_ids, assay_dfs):
            print("AID:", assay_id)
            print(df.head())
            print("-" * 80)

    end = time.time()
    print("Num assay IDs:", len(assay_ids))
    print("Time elapsed:", end - start)
