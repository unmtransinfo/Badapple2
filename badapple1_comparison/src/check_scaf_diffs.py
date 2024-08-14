"""
@author Jack Ringer (+GitHub copilot)
Date: 8/14/2024
Description:
Script to check that differences in scaffold annotations are solely
due to differences in compound<-> scaffold relationships.

Run sql/compare_compound_scaf_relationships.sql and sql/compare_scaffold_stats.sql
BEFORE running this script.
"""

import argparse

import pandas as pd


# Function to count occurrences of scafsmi in a column with comma-separated values
def count_occurrences(scafsmi, column):
    count = 0
    for entry in column:
        if pd.notna(entry):  # Check if the entry is not NaN
            count += entry.split(",").count(scafsmi)
    return count


def parse_args():
    parser = argparse.ArgumentParser(description="Check scaffold differences.")
    parser.add_argument(
        "--scaffold_stats_filepath",
        type=str,
        default="scaffold_compare_stats.csv",
        help="Path to the scaffold_compare_stats.csv file",
    )
    parser.add_argument(
        "--compound_diff_filepath",
        type=str,
        default="compound-scaffold_differences.tsv",
        help="Path to the compound-scaffold_differences.tsv file",
    )
    return parser.parse_args()


def main(args):
    scaffold_stats_df = pd.read_csv(args.scaffold_stats_filepath)
    compound_diff_df = pd.read_csv(args.compound_diff_filepath, sep="\t")

    total_unexpected = 0
    for index, row in scaffold_stats_df.iterrows():
        ncpd_total_badapple = row["ncpd_total_badapple"]
        ncpd_total_comparison = row["ncpd_total_comparison"]

        if ncpd_total_badapple != ncpd_total_comparison:
            scafsmi = row["scafsmi"]
            expected_count = abs(ncpd_total_badapple - ncpd_total_comparison)
            badapple_count = count_occurrences(
                scafsmi, compound_diff_df["badapple_scafsmis"]
            )
            comparison_count = count_occurrences(
                scafsmi, compound_diff_df["badapple_comparison_scafsmis"]
            )
            if ncpd_total_comparison > ncpd_total_badapple:
                actual_count = comparison_count - badapple_count
            else:
                actual_count = badapple_count - comparison_count

            if actual_count < expected_count:
                print(f"Row {index} does not follow the expected pattern:")
                print(row)
                print(
                    f"Expected count: {expected_count}, Actual count: {actual_count}\n"
                )
                total_unexpected += 1
    print(
        f"Found {total_unexpected} rows where differences between 'ncpd_total_badapple' and 'ncpd_total_comparison' were not explained by differences in compound-scaffold relationships."
    )


if __name__ == "__main__":
    args = parse_args()
    main(args)
