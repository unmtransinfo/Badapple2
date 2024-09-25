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
        "--data_source_category",
        type=str,
        default="",
        help="(Optional) Will filter by the provided data source category (e.g. 'NIH Initiatives'). If given, you'll need to provide pubchem_data_sources_file.",
    )
    parser.add_argument(
        "--pubchem_data_sources_file",
        type=str,
        default="",
        help="Path to file downloaded from: https://pubchem.ncbi.nlm.nih.gov/sources/#sort=Last-Updated-Latest-First. Required if using data_source_category.",
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
    if len(args.data_source_category) > 0 and len(args.pubchem_data_sources_file) < 1:
        raise ValueError(
            f"Provided data_source_category but not a path to pubchem_data_sources_file."
        )
    logger.info(f"Reading bioassays.tsv.gz...")
    bioassays_df = pd.read_csv(args.bioassays_file, compression="gzip", sep="\t")
    # filter out non-HTS assays
    logger.info(f"Filtering by N_compounds >= {args.n_compound_thresh}")
    bioassays_df = bioassays_df[
        bioassays_df["Number of Tested CIDs"] >= args.n_compound_thresh
    ]
    logger.info(f"Filtering by Outcome Type == Screening")
    bioassays_df = bioassays_df[bioassays_df["Outcome Type"] == "Screening"]
    if len(args.data_source_category) > 0:
        logger.info(f"Filtering by Data Source Category: {args.data_source_category}")
        data_sources_df = pd.read_csv(args.pubchem_data_sources_file, sep=",")
        data_sources_df = data_sources_df.dropna(subset=["Source Category"])
        # using contains bc often the Source Category contains multiple labels, for example: "Legacy Depositors, NIH Initiatives"
        data_sources_df = data_sources_df[
            data_sources_df["Source Category"].str.contains(args.data_source_category)
        ]
        bioassays_df = bioassays_df = bioassays_df[
            bioassays_df["Source Name"].isin(data_sources_df["Source Name"])
        ]
    # get and save list of HTS AIDs
    hts_aids_list = bioassays_df["AID"].tolist()
    with open(args.aid_out_file, "w") as file:
        for aid in hts_aids_list:
            file.write(f"{aid}\n")
    logger.info(f"Done! Wrote AID list to: {args.aid_out_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Filter assay ids based on HTS criteria.",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
