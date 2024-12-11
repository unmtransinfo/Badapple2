"""
@author Jack Ringer
Date: 11/19/2024
Description:
File which combines outputs from 'pubchem_assay_descriptions.py'
and 'pubchem_assay_annotations.py' to create the aid2descriptors table
for the Badapple2 DB.
"""

import argparse

import pandas as pd

from utils.file_utils import load_json_file


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--descriptions_json_file",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="Path to JSON file with assay descriptions (from pubchem_assay_descriptions.py)",
    )
    parser.add_argument(
        "--annotations_json_file",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="Path to JSON file with assay annotations (from pubchem_assay_annotations.py)",
    )
    parser.add_argument(
        "--tsv_out_path",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="Path to save the aid2descriptors table to in TSV format",
    )
    parser.add_argument(
        "--annotations_sourcename",
        type=str,
        default="BioAssay Research Database (BARD)",
        help="Annotation data will be restricted to this source only.",
    )
    return parser.parse_args()


def get_source_ref_num(aid_ref_list: list[dict], source: str) -> int:
    for ref in aid_ref_list:
        if "SourceName" in ref and ref["SourceName"] == source:
            return ref["ReferenceNumber"]
    return -1


def get_aid2annotations(
    ann_data: dict[str, dict],
    source_name: str,
    source_annotation_types: list[str],
) -> dict[str, list[str]]:
    # get annnotations for a particular source

    # first label annotations which come from desired source
    aid2refnum = {}
    for aid in ann_data["References"]:
        aid2refnum[aid] = get_source_ref_num(
            ann_data["References"][aid], args.annotations_sourcename
        )

    # then gather annotations with the correct refnum
    aid2sourceannotations = {}
    for aid, ref_n in aid2refnum.items():
        aid2sourceannotations[aid] = {}
        if ref_n == -1:
            # AID not in source
            for ann_type in source_annotation_types:
                aid2sourceannotations[aid] = {
                    ann_type: None for ann_type in source_annotation_types
                }
        else:
            # AID has entry in source
            aid_all_annotations = ann_data["Annotations"][aid]
            remaining_terms = source_annotation_types.copy()
            for annotation in aid_all_annotations:
                if annotation["ReferenceNumber"] == ref_n:
                    ann_type = annotation["Name"]
                    ann_val = annotation["Value"]
                    aid2sourceannotations[aid][ann_type] = ann_val
                    remaining_terms.remove(ann_type)
            # for partially-labeled entries
            for ann_type in remaining_terms:
                aid2sourceannotations[aid][ann_type] = None
    return aid2sourceannotations


def main(args):
    if args.annotations_sourcename != "BioAssay Research Database (BARD)":
        # annotation types and so on are particular to each source
        raise ValueError(f"Currently only BARD supported as annotations_sourcename")

    # place json data into dicts
    description_data = load_json_file(args.descriptions_json_file)
    annotation_data = load_json_file(args.annotations_json_file)

    # filter annotations based on given source
    ANNOTATION_TYPES = ["Assay Format", "Assay Type", "Detection Method"]
    source_annotation_data = get_aid2annotations(
        annotation_data, args.annotations_sourcename, ANNOTATION_TYPES
    )

    # combine annotation and description data
    assert set(description_data.keys()) == set(
        source_annotation_data.keys()
    ), f"Descriptions and annotations should come from same set of assays"
    source_annotation_df = pd.DataFrame.from_dict(
        source_annotation_data, orient="index"
    )
    description_df = pd.DataFrame.from_dict(description_data, orient="index")
    aid2descriptors = description_df.join(source_annotation_df, how="right")
    aid2descriptors.reset_index(inplace=True)
    aid2descriptors.rename(columns={"index": "AID"}, inplace=True)
    aid2descriptors.to_csv(args.tsv_out_path, sep="\t", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Combine assay descriptions/protocols with assay annotations from a given source into aid2descriptors table"
    )
    args = parse_args(parser)
    main(args)
