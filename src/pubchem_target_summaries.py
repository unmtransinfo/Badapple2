"""
@author Jack Ringer
Date: 9/9/2024
Description:
Get info on targets for a given list of PubChem assay ids (AIDs).
The input file is expected to only contain a list of AIDs, with each id
separated by a newline.
"""

import argparse
import json
import os

import pubchempy as pcp
from tqdm import tqdm

from utils.file_utils import read_aid_file


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--aid_file",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="input text file containing assays ids (one id/line)",
    )
    parser.add_argument(
        "--out_json_file",
        type=str,
        default="aid2target.json",
        help="JSON output file mapping AID to list of targets",
    )
    return parser.parse_args()


def main(args):
    if not (args.out_json_file.endswith(".json")):
        raise ValueError(
            f"out_json_file must have JSON filetype, please check arguments. Given filename was: {args.out_json_file}"
        )
    assay_ids = read_aid_file(args.aid_file)

    # get target info for each assay
    aid2target = {}
    for aid in tqdm(assay_ids, desc="Processing list of assay ids..."):
        assay = pcp.Assay.from_aid(aid)
        target_info = assay.target
        aid2target[aid] = target_info

    # save output to JSON file
    out_dir = os.path.dirname(args.out_json_file)
    if out_dir != "":
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out_json_file, "w") as f:
        json.dump(aid2target, f, sort_keys=True, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get info on targets for a given list of PubChem assay ids",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
