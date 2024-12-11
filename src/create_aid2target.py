"""
@author Jack Ringer
Date: 11/15/2024
Description:
Script which generates the TSVs used to populate the "aid2target". Will also generate a targets table without duplicates.
table in the badapple2 DB. Uses output of json_to_tsv.py
Will assign target_id to each unique target in input (requires combining duplicates). 
"""

import argparse
from typing import Tuple

import pandas as pd
from tqdm import tqdm

from utils.target_utils import TargetType, strip_version


def are_duplicates(row1, row2) -> bool:
    # this function somewhat doubles as a duplicate check and a sanity check (particularly for proteins)
    type_1, type_2 = row1["TargetType"], row2["TargetType"]
    if pd.isna(type_1) or pd.isna(type_2) or type_1 != type_2:
        return False
    elif type_1 in TargetType:
        ncbi_1, ncbi_2 = row1["NCBI_ID"], row2["NCBI_ID"]
        if type_1 == TargetType.PROTEIN.value:
            uni_1, uni_2 = row1["UniProtID"], row2["UniProtID"]
            if not (pd.isna(uni_1) or pd.isna(uni_2)) and uni_1 == uni_2:
                return True
            # fall back on NCBI_ID comparison if either uniprot id null
        return ncbi_1 == ncbi_2
    raise ValueError(f"Unrecognized target type in row: {row1}")


def get_target_tables(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # not the most efficient way to do this, but works for
    # the relatively small dataset we're working with

    # combine duplicates / create "target" table
    indices_to_drop = set()
    dropped_to_first = {}
    for i in tqdm(range(len(df)), "Processing duplicates"):
        if i in indices_to_drop:
            continue
        for j in range(i + 1, len(df)):
            if j not in indices_to_drop and are_duplicates(df.iloc[i], df.iloc[j]):
                indices_to_drop.add(j)
                dropped_to_first[j] = i

    target_df = df.drop(index=indices_to_drop)
    target_df.drop("AID", axis=1, inplace=True)
    target_df["TargetID"] = list(range(1, len(target_df) + 1))

    # now that duplicates combined can assign id map between AID and targets
    # TargetID is unique to badapple2 DB (can't use NCBI_ID because depositor info is inconsistent, e.g. some use UniProtID others use NIH accession etc)
    aid2target = []
    pair_seen = set()
    for i in tqdm(range(len(df)), "Creating aid2target table"):
        aid = df.at[i, "AID"]
        was_dropped = i in indices_to_drop
        if was_dropped and not ((aid, dropped_to_first[i]) in pair_seen):
            first_i = dropped_to_first[i]
            pair_seen.add((aid, first_i))
            aid2target.append((aid, target_df.at[first_i, "TargetID"]))
        elif not (was_dropped) and not ((aid, i) in pair_seen):
            pair_seen.add((aid, i))
            aid2target.append(
                (aid, target_df.at[i, "TargetID"])
            )  # note we did not reset index

    aid2target_df = pd.DataFrame(aid2target, columns=["AID", "TargetID"])
    return target_df, aid2target_df


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--inp_tsv",
        type=str,
        help="Path to input targets TSV file (output of json_to_tsv.py).",
    )
    parser.add_argument(
        "--unique_target_out_path",
        type=str,
        help="Path to output TSV file for targets TSV without duplicates",
    )
    parser.add_argument(
        "--aid2target_out_path",
        type=str,
        help="Path to output TSV file for aid2target table",
    )
    args = parser.parse_args()
    return args


def main(args):
    input_df = pd.read_csv(args.inp_tsv, sep="\t")
    input_df.dropna(
        subset=["NCBI_ID"], inplace=True
    )  # if NCBI_ID is NaN then target was not specified
    input_df.reset_index(inplace=True, drop=True)
    # remove versioning information, not useful for our case
    input_df["NCBI_ID"] = input_df["NCBI_ID"].apply(strip_version)

    # merge duplicates and get aid2target table
    unique_target_df, aid2target_df = get_target_tables(input_df)
    unique_target_df.to_csv(args.unique_target_out_path, sep="\t", index=False)
    aid2target_df.to_csv(args.aid2target_out_path, sep="\t", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Combine duplicate target entries from input TSV into single row, output result to TSV file."
    )
    args = parse_args(parser)
    main(args)
