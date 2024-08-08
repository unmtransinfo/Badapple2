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
        "--assay_zip_dir",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="path to directory containing assay .zip files",
    )
    parser.add_argument(
        "--o_compound",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="output TSV file with all compound ids (CIDs) and their isomeric SMILES (from PubChem data). Will be the union of all CIDs present in the given assays.",
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
    parser.add_argument(
        "--process_by_batch",
        help="Process given AID file by .zip rather than by AID. Faster, but requires more memory (process will be killed if OOM occurs).",
        action=argparse.BooleanOptionalAction,
        default=False,
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
    zip_filepath: str,
    assay_ids: list[int],
    col_types: dict,
    logger,
) -> list[pd.DataFrame]:
    zip_filename = os.path.splitext(os.path.basename(zip_filepath))[0]
    dfs = []
    cols = list(col_types.keys())
    try:
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
    except Exception as e:
        logger.info(f"Assay id(s): {assay_ids}")
        logger.info(f".zip file: {zip_filepath}")
        raise e
    return dfs


def activity_to_code(activity_str: str) -> int:
    if activity_str == "Inactive":
        return 1
    elif activity_str == "Active":
        return 2
    elif activity_str == "Inconclusive":
        return 3
    elif activity_str == "Unspecified" or pd.isna(activity_str):
        return 4
    elif activity_str == "Probe":
        return 5
    else:
        raise ValueError("Unrecognized activity_str:", activity_str)


def write_dfs(
    assay_dfs: list[pd.DataFrame],
    assay_ids: list[int],
    compounds_writer,
    sid2cid_writer,
    astats_writer,
    written_sid2cid_pairs: set,
    written_cids: set,
):
    assert len(assay_dfs) == len(assay_ids)
    for assay_id, df in zip(assay_ids, assay_dfs):
        df["AID"] = assay_id
        df["PUBCHEM_ACTIVITY_OUTCOME"] = df["PUBCHEM_ACTIVITY_OUTCOME"].map(
            activity_to_code
        )
        compound_rows = df[["PUBCHEM_CID", "PUBCHEM_EXT_DATASOURCE_SMILES"]]
        compound_rows = (
            compound_rows.drop_duplicates()
        )  # there can be multiple CIDs/AID (same CID, different SID)
        compound_rows = compound_rows.values
        sid2cid_rows = df[["PUBCHEM_SID", "PUBCHEM_CID"]].values
        astats_rows = df[["AID", "PUBCHEM_SID", "PUBCHEM_ACTIVITY_OUTCOME"]].values

        # filter out duplicates
        new_sid2cid_rows = [
            row for row in sid2cid_rows if tuple(row) not in written_sid2cid_pairs
        ]
        new_cid_rows = [row for row in compound_rows if tuple(row) not in written_cids]
        written_sid2cid_pairs.update(tuple(row) for row in new_sid2cid_rows)
        written_cids.update(tuple(row) for row in new_cid_rows)

        # write to files
        compounds_writer.writerows(new_cid_rows)
        sid2cid_writer.writerows(new_sid2cid_rows)
        astats_writer.writerows(astats_rows)


def batch_process(
    args,
    assay_ids: list[int],
    col_types: list[str],
    compounds_writer,
    sid2cid_writer,
    astats_writer,
    written_sid2cid_pairs: set,
    written_cids: set,
    logger,
):
    # process assays by .zip file
    # faster but more demanding memory-wise
    zip2aids = {}
    for aid in assay_ids:
        zip_filename = get_zip_filename(aid)
        zip2aids[zip_filename] = zip2aids.get(zip_filename, []) + [aid]

    for zip_filename, zip_assay_ids in tqdm(zip2aids.items()):
        zip_filepath = os.path.join(args.assay_zip_dir, zip_filename)
        assay_dfs = read_csv_files(zip_filepath, zip_assay_ids, col_types, logger)
        write_dfs(
            assay_dfs,
            zip_assay_ids,
            compounds_writer,
            sid2cid_writer,
            astats_writer,
            written_sid2cid_pairs,
            written_cids,
        )


def single_process(
    args,
    assay_ids: list[int],
    col_types: list[str],
    compounds_writer,
    sid2cid_writer,
    astats_writer,
    written_sid2cid_pairs: set,
    written_cids: set,
    logger,
):
    # process assays by AID, one at a time
    for aid in tqdm(assay_ids):
        zip_filename = get_zip_filename(aid)
        zip_filepath = os.path.join(args.assay_zip_dir, zip_filename)
        # singleton list
        assay_dfs = read_csv_files(zip_filepath, [aid], col_types, logger)
        write_dfs(
            assay_dfs,
            [aid],
            compounds_writer,
            sid2cid_writer,
            astats_writer,
            written_sid2cid_pairs,
            written_cids,
        )


def main(args):
    logger = get_and_set_logger(args.log_fname)
    assay_ids = read_aid_file(args.aid_file)

    # keep track of already written SID-CID pairs and written CIDs
    written_sid2cid_pairs = set()
    written_cids = set()

    # create writers
    compounds_writer, f_compounds = get_csv_writer(args.o_compound, "\t")
    sid2cid_writer, f_sid2cid = get_csv_writer(args.o_sid2cid, "\t")
    astats_writer, f_astats = get_csv_writer(args.o_assaystats, "\t")
    compounds_writer.writerow(["CID", "ISOMERIC_SMILES"])
    sid2cid_writer.writerow(["SID", "CID"])
    astats_writer.writerow(["AID", "SID", "ACTIVITY_OUTCOME"])

    # COL_TYPES = columns required for our output files
    COL_TYPES = {
        "PUBCHEM_SID": "Int64",
        "PUBCHEM_CID": "Int64",
        "PUBCHEM_EXT_DATASOURCE_SMILES": str,
        "PUBCHEM_ACTIVITY_OUTCOME": str,
    }
    if args.process_by_batch:
        logger.info("Processing AID files (by .zip)...")
        batch_process(
            args,
            assay_ids,
            COL_TYPES,
            compounds_writer,
            sid2cid_writer,
            astats_writer,
            written_sid2cid_pairs,
            written_cids,
            logger,
        )
    else:
        logger.info("Processing AID files...")
        single_process(
            args,
            assay_ids,
            COL_TYPES,
            compounds_writer,
            sid2cid_writer,
            astats_writer,
            written_sid2cid_pairs,
            written_cids,
            logger,
        )

    close_file(f_compounds)
    close_file(f_sid2cid)
    close_file(f_astats)
    logger.info("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get results from all assays in given assay id (AID) file",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
