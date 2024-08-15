"""
Author: Jack Ringer (+copilot)
Date: 8/15/2024
Description:
Script for generating 'in_drug' labels in 'scaffold' table.

Intended to imitate:
https://github.com/unmtransinfo/Badapple/blob/master/python/drug_scafs_2sql.py
"""

import argparse

import psycopg2
from psycopg2 import sql
from tqdm import tqdm


# Function to parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(
        description="Annotate in_drug field in scaffold table."
    )
    parser.add_argument("--dbname", required=True, help="Name of the database")
    parser.add_argument("--user", required=True, help="Database user")
    parser.add_argument("--password", required=True, help="Database password")
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument(
        "--scaf_file_path",
        required=True,
        help="Path to the scaffolds file",
    )
    parser.add_argument(
        "--dbschema", default="public", help="Database schema (default: public)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    # Database connection parameters
    db_params = {
        "dbname": args.dbname,
        "user": args.user,
        "password": args.password,
        "host": args.host,
    }

    input_file_path = args.scaf_file_path
    dbschema = args.dbschema
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # Open the input file
        with open(input_file_path, "r") as file:
            n_in = 0
            n_out = 0

            # Loop through each line in the input file
            print("Updating in_drug...")
            for line in tqdm(file, desc="Processing lines"):
                n_in += 1

                # Skip header, empty lines, and comments
                if (
                    not line.strip()
                    or line.startswith("#")
                    or line.startswith("scaffold")
                ):
                    continue

                # Extract the SMILES string from the second column
                smi = line.split("\t")[1].strip()

                # Generate the SQL UPDATE statement using rdkit cartridge
                update_query = sql.SQL(
                    "UPDATE {dbschema}.scaffold SET in_drug=TRUE "
                    "FROM mols_scaf WHERE mols_scaf.scafmol @= {smi}::mol "
                    "AND scaffold.id = mols_scaf.id"
                ).format(dbschema=sql.Identifier(dbschema), smi=sql.Literal(smi))

                # Execute the SQL UPDATE statement
                cur.execute(update_query)
                n_out += 1

            # Set in_drug to FALSE where it is NULL
            update_false_query = sql.SQL(
                "UPDATE {dbschema}.scaffold SET in_drug=FALSE WHERE in_drug IS NULL"
            ).format(dbschema=sql.Identifier(dbschema))
            cur.execute(update_false_query)

            # Commit the transaction
            conn.commit()

            # Print the summary
            print(f"in_drug_annotate.sql: lines in: {n_in} ; converted to sql: {n_out}")

    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
