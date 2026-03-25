import argparse

import pandas as pd
from medchem.structural.lilly_demerits import LillyDemeritsFilters
from rdkit import Chem


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
        "--n_jobs",
        type=int,
        default=0,
        help="Number of processes to use: 0 to force sequential, -1 to use all available",
    )
    return parser.parse_args()


def read_df(fpath: str, delim: str, header: bool) -> pd.DataFrame:
    # TODO: remove nrows, just using for testing
    if header:
        df = pd.read_csv(fpath, sep=delim, nrows=10_000)
    else:
        df = pd.read_csv(fpath, sep=delim, header=None, nrows=10_000)
    return df


def main(args):
    dfilters = LillyDemeritsFilters(allow_non_interesting=False)
    cpd_df = read_df(args.input_dsv_file, args.idelim, args.iheader)
    smiles_col_name = cpd_df.columns[args.smiles_column]
    names_col_name = cpd_df.columns[args.name_column]
    cpd_df = cpd_df[[names_col_name, smiles_col_name]]

    res_df = dfilters(
        mols=cpd_df[smiles_col_name].to_list(),
        progress=True,
        n_jobs=args.n_jobs,
    )
    res_df.drop(
        "smiles", axis=1, inplace=True
    )  # 'smiles' contains converted SMILES, 'mol' given SMILES
    res_df.rename(columns={"mol": "smiles"}, inplace=True)
    res_df = res_df.merge(
        cpd_df,
        left_on="smiles",
        right_on=smiles_col_name,
        how="left",
    )
    if smiles_col_name != "smiles":
        # drop redundant col
        res_df.drop(smiles_col_name, axis=1, inplace=True)
    res_df.to_csv(args.output_tsv, sep="\t", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply LillyDemeritsFilters to input SMILES file (can be CSV, TSV, etc)",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
