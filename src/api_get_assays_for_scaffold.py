"""
@author Jack Ringer
Date: 10/15/2024
Description:
For a given scaffold ID, save a text file with the set of all PubChem
assay IDs (AID) associated with the scaffold.
"""

import argparse
import json

import requests

from utils.file_utils import write_aid_file


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--scafid",
        type=int,
        required=True,
        default=argparse.SUPPRESS,
        help="ID of scaffold in Badapple DB",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="path to output file (list of AIDs)",
    )
    return parser.parse_args()


def main(args):
    # TODO: update from localhost to actual website once API deployed
    API_URL = "http://localhost:8000/api/v1/scaffold_search/get_associated_assay_ids"
    response = requests.get(API_URL, params={"scafid": args.scafid})
    aid_list = json.loads(response.text)
    write_aid_file(aid_list, args.output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get .aid file with associated assays for given scaffold.",
        epilog="",
    )
    print("Working...")
    args = parse_args(parser)
    main(args)
