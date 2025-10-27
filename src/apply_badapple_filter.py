"""
@author Jack Ringer
Date: 11/26/2024
Description:
With an input CSV/TSV file containing scaffold scores generated for a set of compounds
(e.g., from api_scripts/api_get_compound_scores.py), apply filters based on pScore + inDB
columns to indicate if each compound is considered a risk or not.
"""

import argparse

import pandas as pd

from utils.file_utils import read_input_compound_df


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--input_tsv",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="input CSV/TSV file containing compounds and their corresponding scaffold info from badapple",
    )
    parser.add_argument(
        "--output_tsv",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="output TSV file with compound information (name,smiles) and whether the compound passed the filter",
    )
    parser.add_argument(
        "--idelim",
        type=str,
        default="\t",
        help="delim for input file (default is tab)",
    )
    parser.add_argument(
        "--iheader",
        action="store_true",
        help="input file has header line",
    )
    parser.add_argument(
        "--smiles_column",
        type=int,
        default=0,
        help="(integer) column where SMILES are located (for input file)",
    )
    parser.add_argument(
        "--name_column",
        type=int,
        default=1,
        help="(integer) column where molecule names are located (for input file). Names should be unique!",
    )
    parser.add_argument(
        "--pscore_column",
        type=int,
        default=2,
        help="(integer) column of pscores",
    )
    parser.add_argument(
        "--inDrug_column",
        type=int,
        default=3,
        help="(integer) column of inDrug",
    )
    parser.add_argument(
        "--inDB_column",
        type=int,
        default=4,
        help="(integer) column indicating if scaffold was in badapple DB",
    )
    parser.add_argument(
        "--pscore_max",
        type=float,
        default=300,
        help="fail scaffolds with pScore>=pscore_max (unless inDrug=True)",
    )
    parser.add_argument(
        "--ignore_inDrug",
        action="store_true",
        help="ignore inDrug criteria (only use pScores)",
    )
    return parser.parse_args()


def passes_filter(
    row,
    in_db_col: bool,
    pscore_col: str,
    inDrug_col: str,
    pscore_max: float,
    ignore_inDrug: bool,
):
    if pd.isna(row[in_db_col]) or not (row[in_db_col]):
        return True  # no scaffold or scaffold was not in DB - no information so pass

    if pd.isna(row[pscore_col]):
        return True  # scaffold is in DB, but not enough evidence to assign a pScore so pass

    # assume we have inDrug and pScore info now
    if ignore_inDrug:
        return row[pscore_col] < pscore_max
    return row[pscore_col] < pscore_max or row[inDrug_col]


def main(args):
    df = read_input_compound_df(
        args.input_tsv, args.idelim, args.iheader, args.smiles_column, args.name_column
    )
    smiles_col = df.columns[args.smiles_column]
    names_col = df.columns[args.name_column]
    pscore_col = df.columns[args.pscore_column]
    inDrug_col = df.columns[args.inDrug_column]
    in_db_col = df.columns[args.inDB_column]
    filter_col_name = "passesFilter"
    for _, sub_df in df.groupby(names_col):
        # sub_df is a dataframe for a given compound (based on name) and all its scaffolds + their info from badapple
        filter_results = sub_df.apply(
            lambda row: passes_filter(
                row,
                in_db_col,
                pscore_col,
                inDrug_col,
                args.pscore_max,
                args.ignore_inDrug,
            ),
            axis=1,
        )
        # all scaffolds should pass
        passed_filter = filter_results.all()
        df.loc[sub_df.index, filter_col_name] = passed_filter
    # write output
    df = df[[smiles_col, names_col, filter_col_name]]
    df = df.drop_duplicates(subset=names_col)
    df.to_csv(args.output_tsv, sep="\t", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply filter to compounds based on badapple criteria (scaffold pscore + in_drug). Compounds with no scaffolds will automatically pass.",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
