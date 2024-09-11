"""
@author Jack Ringer
Date: 9/10/2024
Description:
Fetch bioassay annotations for a list of assay ids. Annotations
can provide information relevant to bioassay ontology (e.g., assay type, format, etc)
"""

import argparse
import json
import os

import requests
from tqdm import tqdm

from utils.file_utils import read_aid_file


def get_assay_data(aid: int) -> dict:
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/assay/{aid}/JSON"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        return data
    print(f"Failed to retrieve data for AID {aid}")
    return {}


def process_annotation_info(annotation_info: dict):
    def _extract_string(item):
        if "Value" in item and "StringWithMarkup" in item["Value"]:
            item["Value"] = item["Value"]["StringWithMarkup"][0]["String"]
        return item

    return list(map(_extract_string, annotation_info))


def get_assay_annotations(data: dict):
    sections = data.get("Record", {}).get("Section", [])
    for section in sections:
        if section.get("TOCHeading") == "BioAssay Annotations":
            annotation_info = section["Information"]
            # get rid of wrappers around value
            return process_annotation_info(annotation_info)
    return None


def get_assay_references(data: dict):
    return data.get("Record", {}).get("Reference", [])


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
        help="JSON output file with assay annotations and references for each AID",
    )
    return parser.parse_args()


def main(args):
    if not (args.out_json_file.endswith(".json")):
        raise ValueError(
            f"out_json_file must have JSON filetype, please check arguments. Given filename was: {args.out_json_file}"
        )
    assay_ids = read_aid_file(args.aid_file)

    # get annotation/ref info for each assay
    assay_info = {"Annotations": {}, "References": {}}
    for aid in tqdm(assay_ids, desc="Processing list of assay ids..."):
        data = get_assay_data(aid)
        annotations = get_assay_annotations(data)
        references = get_assay_references(data)
        assay_info["Annotations"][aid] = annotations
        assay_info["References"][aid] = references

    # save output to JSON file
    out_dir = os.path.dirname(args.out_json_file)
    if out_dir != "":
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out_json_file, "w") as f:
        json.dump(assay_info, f, sort_keys=True, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get info relevant to assay ontology along with references",
        epilog="",
    )
    args = parse_args(parser)
    main(args)
