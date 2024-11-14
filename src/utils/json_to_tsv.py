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


def unpack_target_json_to_tsv(json_path: str, tsv_path: str):
    # Read JSON file
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
            name = item.get("name", "")
            organism_taxname = (
                item.get("organism", {}).get("org", {}).get("taxname", "")
            )
            is_protein = "protein_accession" in item
            protein_accession = item.get("protein_accession", "") if is_protein else ""
            uniprot_id = item.get("uniprot_id", "") if is_protein else ""

            # Append row to list
            rows.append(
                [aid, name, organism_taxname, is_protein, protein_accession, uniprot_id]
            )

    # Create DataFrame
    df = pd.DataFrame(
        rows,
        columns=[
            "AID",
            "Name",
            "Organism TaxName",
            "isProtein",
            "Protein Accession",
            "UniProt ID",
        ],
    )

    df["AID"] = pd.to_numeric(df["AID"], errors="coerce").astype("Int64")
    # Sort DataFrame by AID column
    df = df.sort_values(by="AID")

    # Save DataFrame to TSV
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
