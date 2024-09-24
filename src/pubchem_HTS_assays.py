"""
@author Jack Ringer
Date: 9/24/2024
Description:
This scripts generates a text file with the list of AIDs that are considered
high-throughput screening (HTS).

Run sh_scripts/mirror_pubchem.sh BEFORE using this script.
"""

import argparse

import pandas as pd

from utils.custom_logging import get_and_set_logger


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--bioassays_file",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="Path to bioassays.tsv.gz file from PubChem. Use sh_scripts/mirror_pubchem.sh to generate.",
    )
    parser.add_argument(
        "--aid_out_file",
        type=str,
        default="HTS_assays.aid",
        help="output text file containing assay ids considered HTS (one id/line)",
    )
    parser.add_argument(
        "--n_compound_thresh",
        type=int,
        default=20_000,
        help="Compound threshold for considering an assay HTS. Assays with >= n_compound_thresh unique compounds will be considered HTS.",
    )
    parser.add_argument(
        "--log_fname",
        help="File to save logs to. If not given will log to stdout.",
        default=None,
    )
    return parser.parse_args()


def main(args):
    logger = get_and_set_logger(args.log_fname)
    if not args.bioassays_file.endswith("bioassays.tsv.gz"):
        raise ValueError(
            f"--bioassays_file should be path to the bioassays.tsv.gz file downloaded from PubChem, given: {args.bioassays_file}"
        )
    logger.info(f"Reading bioassays.tsv.gz...")
    bioassays_df = pd.read_csv(args.bioassays_file, compression="gzip", sep="\t")
    # filter out non-HTS assays
    bioassays_df = bioassays_df[
        bioassays_df["Number of Tested CIDs"] >= args.n_compound_thresh
    ]
    # get and save list of HTS AIDs
    hts_aids_list = bioassays_df["AID"].tolist()
    with open(args.aid_out_file, "w") as file:
        for aid in hts_aids_list:
            file.write(f"{aid}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter assay ids based on HTS criteria.",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
