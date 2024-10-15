"""
@author Jack Ringer
Date: 10/15/2024
Description:
Fetch raw description text for a given list of assay ids.
"""

import argparse
import json
import os

import requests
from tqdm import tqdm

from utils.file_utils import read_aid_file


def get_assay_description(aid: int) -> str:
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/{aid}/description/JSON"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        description_list = data["PC_AssayContainer"][0]["assay"]["descr"]["description"]
        return "\n".join(description_list)  # create single description string
    print(f"Failed to retrieve data for AID {aid}")
    return ""


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
        help="JSON output file with description text for each assay ID.",
    )
    return parser.parse_args()


def main(args):
    if not (args.out_json_file.endswith(".json")):
        raise ValueError(
            f"out_json_file must have JSON filetype, please check arguments. Given filename was: {args.out_json_file}"
        )
    assay_ids = read_aid_file(args.aid_file)

    # get description for each assay
    descriptions = {}
    for aid in tqdm(assay_ids, desc="Processing list of assay ids..."):
        descriptions[aid] = get_assay_description(aid)

    # save output to JSON file
    out_dir = os.path.dirname(args.out_json_file)
    if out_dir != "":
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out_json_file, "w") as f:
        json.dump(descriptions, f, sort_keys=True, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get assay descriptions from PubChem",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
