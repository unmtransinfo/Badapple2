"""
@author Jack Ringer
Date: 9/27/2024
Description:
Helper utils to convert annotations and target JSON files to TSV for easier readability.
"""

import argparse
import json

import pandas as pd


def unpack_annotations_json_to_tsv(json_path: str, tsv_path: str):
    # Load JSON data
    with open(json_path, "r") as file:
        data = json.load(file)

    # Prepare lists to store the rows
    rows = []

    # Iterate through each AID
    for aid, annotations in data["Annotations"].items():
        references = data["References"].get(aid, [])

        # Handle null or empty annotations and references
        if not annotations:
            rows.append([aid, None, None, None, None, None])
        else:
            for annotation in annotations:
                # Find the matching reference
                reference = next(
                    (
                        ref
                        for ref in references
                        if ref["ReferenceNumber"] == annotation["ReferenceNumber"]
                    ),
                    None,
                )
                rows.append(
                    [
                        aid,
                        annotation.get("Name"),
                        annotation.get("Value"),
                        reference.get("SourceName") if reference else None,
                        reference.get("SourceID") if reference else None,
                        (
                            int(reference.get("ANID"))
                            if reference and reference.get("ANID") is not None
                            else None
                        ),
                    ]
                )

    # Create DataFrame
    df = pd.DataFrame(
        rows,
        columns=[
            "AID",
            "Annotation Name",
            "Annotation Value",
            "Reference SourceName",
            "Reference SourceID",
            "Reference ANID",
        ],
    )
    # convert numeric columns with NaN to int
    cols = [
        "AID",
        "Reference SourceID",
        "Reference ANID",
    ]
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Sort DataFrame by AID column
    df = df.sort_values(by="AID")
    # Save DataFrame to TSV
    df.to_csv(tsv_path, sep="\t", index=False)


def get_taxonomy_with_common_name(taxid: int):
    # these are from the NCBI:
    # https://www.ncbi.nlm.nih.gov/taxonomy/
    # given small number of missing entries in original set don't have to
    # include many taxids, but for larger DB would want to rethink this
    if taxid == 9606:
        return "Homo sapiens (human)"
    elif taxid == 11269:
        return "Orthomarburgvirus marburgense (Marburg virus)"
    elif taxid == "" or taxid is None:
        return ""  # not specified
    Warning(f"Unrecognized taxid: {taxid}")
    return ""


def unpack_target_json_to_tsv(json_path: str, tsv_path: str):
    with open(json_path, "r") as file:
        data = json.load(file)

    # Initialize list for rows
    rows = []

    # Iterate through JSON data
    for aid, items in data.items():
        if items is None or len(items) == 0:
            rows.append([aid, None, None, None, None, None])  # no target
            continue
        for item in items:
            name = item["Name"]
            target_type = item["TargetType"]
            pubchem_id = item["PubChemID"]
            organism_taxonomy = item["Taxonomy"]
            taxonomy_id = item["TaxonomyID"]
            if "(" not in organism_taxonomy:
                # PubChem API will fill in common name in parens, but if could not fetch
                # info using PubChemAPI (e.g., for nucleotides/pathways) then common name
                # info was not included, so including here
                organism_taxonomy = get_taxonomy_with_common_name(taxonomy_id)
            uniprot_id = item.get(
                "UniProtID", ""
            )  # not included for non-protein entries

            rows.append(
                [
                    aid,
                    name,
                    organism_taxonomy,
                    taxonomy_id,
                    target_type,
                    pubchem_id,
                    uniprot_id,
                ]
            )

    # Create DataFrame
    df = pd.DataFrame(
        rows,
        columns=[
            "AID",
            "Name",
            "Taxonomy",
            "TaxonomyID",
            "TargetType",
            "PubChemID",
            "UniProtID",
        ],
    )

    df["AID"] = pd.to_numeric(df["AID"], errors="coerce").astype("Int64")
    df = df.sort_values(by="AID")
    df.to_csv(tsv_path, sep="\t", index=False)


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument("json_path", type=str, help="Path to the input JSON file.")
    parser.add_argument("tsv_path", type=str, help="Path to the output TSV file.")
    parser.add_argument(
        "conversion_type",
        type=str,
        choices=["annotations", "targets"],
        help="Type of conversion: 'annotations' or 'targets'.",
    )

    args = parser.parse_args()
    return args


def main(args):
    if args.conversion_type == "targets":
        unpack_target_json_to_tsv(args.json_path, args.tsv_path)
    else:
        unpack_annotations_json_to_tsv(args.json_path, args.tsv_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert JSON to TSV.")
    args = parse_args(parser)
    main(args)
