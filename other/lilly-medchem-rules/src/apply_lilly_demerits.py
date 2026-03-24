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
    return parser.parse_args()


def read_df(fpath: str, delim: str, header: bool) -> pd.DataFrame:
    if header:
        df = pd.read_csv(fpath, sep=delim)
    else:
        df = pd.read_csv(fpath, sep=delim, header=None)
    return df


def main(args):
    dfilters = LillyDemeritsFilters()
    cpd_df = read_df(args.input_dsv_file, args.idelim, args.iheader)
    smiles_col_name = cpd_df.columns[args.smiles_column]
    names_col_name = cpd_df.columns[args.name_column]
    res_df = dfilters(
        mols=[Chem.MolFromSmiles(smi) for smi in cpd_df[smiles_col_name].to_list()]
    )
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Apply LillyDemeritsFilters to input SMILES file (can be CSV, TSV, etc)",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
    main(args)
