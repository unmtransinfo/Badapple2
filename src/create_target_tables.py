"""
@author Jack Ringer
Date: 11/15/2024
Description:
Script which generates the TSVs used to populate the "target" and "aid2target"
tables in the badapple2 DB. Uses output of gather_protein_families.py
Will assign target_id to each unique target in input (requires combining duplicates). 
"""

import argparse
from typing import Tuple

import pandas as pd
from tqdm import tqdm

from utils.custom_logging import get_and_set_logger


def are_duplicates(row1, row2) -> bool:
    # this function somewhat doubles as a duplicate check and a sanity check (particularly for proteins)
    type_1, type_2 = row1["TargetType"], row2["TargetType"]
    if pd.isna(type_1) or pd.isna(type_2) or type_1 != type_2:
        return False
    elif type_1 in ["Protein", "Gene", "Nucleotide", "Pathway"]:
        pid_1, pid_2 = row1["PubChemID"], row2["PubChemID"]
        assert not (pd.isna(pid_1)), f"NaN PubChemID in row: {row1}"
        assert not (pd.isna(pid_2)), f"NaN PubChemID in row: {row2}"
        if type_1 == "Protein":
            uni_1, uni_2 = row1["UniProtID"], row2["UniProtID"]
            if pd.isna(uni_1) and pd.isna(uni_2):
                return pid_1 == pid_2
            elif (pid_1 == pid_2) and (uni_1 == uni_2):
                return True
            elif (pid_1 == uni_2) or (uni_1 == pid_2):
                # PubChemID can be UniProtID
                return True
            elif (pid_1 != pid_2) and (uni_1 != uni_2):
                return False
            # generally the PubChemID can be different even though UniProtID is same for these reasons:
            # 1) The two proteins are isoforms
            # 2) The two proteins come from different databases/versions
            # being conservative and considering both cases above to be unique targets (row!=row2)...
            logger.info(
                f"Unusual pattern, falling back on PubChemID comparison alone for the following two rows: \n{row1}\n{row2}"
            )
        return pid_1 == pid_2
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
                # by default use first row - will try to fill in other info if possible
                if pd.isna(df.at[i, "Name"]) and not (pd.isna(df.at[j, "Name"])):
                    df.at[i, "Name"] = df.at[j, "Name"]
                    logger.info(
                        f"Set 'Name' from row 1 to 'Name' from row 2 for the following two rows:\n{df.iloc[i]}\n{df.iloc[j]}"
                    )
                if pd.isna(df.at[i, "OrganismTaxName"]) and not (
                    pd.isna(df.at[j, "OrganismTaxName"])
                ):
                    df.at[i, "OrganismTaxName"] = df.at[j, "OrganismTaxName"]
                    logger.info(
                        f"Set 'OrganismTaxName' from row 1 to the 'OrganismTaxName' from row 2 for the following two rows:\n{df.iloc[i]}\n{df.iloc[j]}"
                    )

    target_df = df.drop(index=indices_to_drop)
    target_df.drop("AID", axis=1, inplace=True)
    target_df["TargetID"] = list(range(1, len(target_df) + 1))

    # now that duplicates combined can assign id map between AID and targets
    # TargetID is unique to badapple2 DB (can't use PubChemID because depositor info is inconsistent, e.g. some use UniProtID others use NIH accession etc)
    aid2target = []
    for i in tqdm(range(len(df)), "Creating aid2target table"):
        aid = df.at[i, "AID"]
        if i in indices_to_drop:
            first_i = dropped_to_first[i]
            aid2target.append((aid, target_df.at[first_i, "TargetID"]))
        else:
            aid2target.append(
                (aid, target_df.at[i, "TargetID"])
            )  # note we did not reset index

    aid2target_df = pd.DataFrame(aid2target, columns=["AID", "TargetID"])
    return target_df, aid2target_df


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--inp_tsv",
        type=str,
        help="Path to input targets TSV file (output of gather_protein_families.py).",
    )
    parser.add_argument(
        "--target_out_path",
        type=str,
        help="Path to output TSV file for target table",
    )
    parser.add_argument(
        "--aid2target_out_path",
        type=str,
        help="Path to output TSV file for aid2target table",
    )
    parser.add_argument(
        "--log_fname",
        help="File to save logs to. If not given will log to stdout.",
        default=None,
    )
    args = parser.parse_args()
    return args


def main(args):
    input_df = pd.read_csv(args.inp_tsv, sep="\t")
    input_df.dropna(
        subset=["PubChemID"], inplace=True
    )  # if PubChemID is NaN then target was not specified
    input_df.reset_index(inplace=True, drop=True)
    target_df, aid2target_df = get_target_tables(input_df)
    target_df.to_csv(args.target_out_path, sep="\t", index=False)
    aid2target_df.to_csv(args.aid2target_out_path, sep="\t", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Combine duplicate target entries from input TSV into single row, output result to TSV file."
    )
    args = parse_args(parser)
    logger = get_and_set_logger(args.log_fname)
    main(args)
