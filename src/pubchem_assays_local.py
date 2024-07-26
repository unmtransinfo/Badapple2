"""
@author Jack Ringer
Date: 7/22/2024
Description:
Script to load and process assay data from local files.
Will generate the Compounds2Substances file (mapping compound id <=> substance id)
+ the Assay stats file (Maps between assay id, substance id, and activity outcome).
These local files were mirrored from PubChem bioassays (https://ftp.ncbi.nlm.nih.gov/pubchem/Bioassay/CSV/Data/)
via rsync (see sh_scripts/mirror_pubchem.sh).
"""

import argparse
import csv
import gzip
import os
import zipfile

import pandas as pd
from loguru import logger
from tqdm import tqdm

from utils.file_utils import close_file, get_csv_writer
from utils.logging import get_and_set_logger


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--aid_file",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="input text file containing assays ids (one id/line)",
    )
    parser.add_argument(
        "--zip_dir",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="path to directory containing assay .zip files",
    )
    parser.add_argument(
        "--o_sid2cid",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="output TSV file which maps compound id (CID) to substance id (SID)",
    )
    parser.add_argument(
        "--o_assaystats",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="output TSV file which maps between assay id (AID), substance id (SID), and activity outcome",
    )
    parser.add_argument(
        "--log_fname",
        help="File to save logs to. If not given will log to stdout.",
        default=None,
    )
    return parser.parse_args()


def read_aid_file(aid_file_path: str) -> list[int]:
    with open(aid_file_path, "r") as file:
        aid_list = [int(line.strip()) for line in file if line.strip().isdigit()]
    return aid_list


def get_zip_filename(
    aid: int, first_aid: int = 1, file_per_zip: int = 1000, num_fill: int = 7
) -> str:
    # <aid>.csv will be contained in file w/ name: <lower>_<upper>.zip
    # where lower <= aid <= upper
    # assuming each .zip contains the same number of files, starting with aid=first_aid
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


def activity_to_code(activity_str: str) -> int:
    if activity_str == "Inactive":
        return 1
    elif activity_str == "Active":
        return 2
    elif activity_str == "Inconclusive":
        return 3
    elif activity_str == "Unspecified":
        return 4
    elif activity_str == "Probe":
        return 5
    else:
        raise ValueError("Unrecognized activity_str:", activity_str)


def main(args):
    assay_ids = read_aid_file(args.aid_file)

    # create writers
    sid2cid_writer, f_sid2cid = get_csv_writer(args.o_sid2cid, "\t")
    astats_writer, f_astats = get_csv_writer(args.o_assaystats, "\t")
    sid2cid_writer.writerow(["SID", "CID"])
    astats_writer.writerow(["AID", "SID", "ACTIVITY_OUTCOME"])

    # COL_TYPES = columns required for our output files
    COL_TYPES = {
        "PUBCHEM_SID": "Int64",
        "PUBCHEM_CID": "Int64",
        "PUBCHEM_EXT_DATASOURCE_SMILES": str,
        "PUBCHEM_ACTIVITY_OUTCOME": str,
    }
    zip2aids = {}
    logger.info("Creating map from zip file -> [assay ids]")
    for aid in assay_ids:
        zip_filename = get_zip_filename(aid)
        zip2aids[zip_filename] = zip2aids.get(zip_filename, []) + [aid]

    logger.info("Processing data by zip file...")
    for zip_filename, assay_ids in tqdm(zip2aids.items()):
        zip_filepath = os.path.join(args.zip_dir, zip_filename)
        assay_dfs = read_csv_files(zip_filepath, assay_ids, COL_TYPES)
        for assay_id, df in zip(assay_ids, assay_dfs):
            df["AID"] = assay_id
            df["PUBCHEM_ACTIVITY_OUTCOME"] = df["PUBCHEM_ACTIVITY_OUTCOME"].map(
                activity_to_code
            )
            sid2cid_rows = df[["PUBCHEM_SID", "PUBCHEM_CID"]].values
            astats_rows = df[["AID", "PUBCHEM_SID", "PUBCHEM_ACTIVITY_OUTCOME"]].values
            sid2cid_writer.writerows(sid2cid_rows)
            astats_writer.writerows(astats_rows)

    close_file(f_sid2cid)
    close_file(f_astats)
    logger.info("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Show assay info using assay id (AID) file", epilog=""
    )
    args = parse_args(parser)
    logger = get_and_set_logger(args.log_fname)
    main(args)
