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

from utils.custom_logging import get_and_set_logger


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
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (use -vv for more verbose)",
    )
    parser.add_argument(
        "--log_fname",
        help="File to save logs to. If not given will log to stdout.",
        default=None,
    )
    return parser.parse_args()


def main(args):
    dbschema = args.dbschema
    try:
        db_connection = psycopg2.connect(
            dbname=args.dbname,
            host=args.host,
            user=args.user,
            password=args.password,
        )
        cur = db_connection.cursor()

        with open(args.scaf_file_path, "r") as file:
            n_in = 0
            n_out = 0

            # Loop through each line in the input file
            logger.info("Updating in_drug...")
            for line in file:
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

            update_false_query = sql.SQL(
                "UPDATE {dbschema}.scaffold SET in_drug=FALSE WHERE in_drug IS NULL"
            ).format(dbschema=sql.Identifier(dbschema))
            cur.execute(update_false_query)

            db_connection.commit()

            # Print the summary
            logger.info(
                f"in_drug_annotate.sql: lines in: {n_in} ; converted to sql: {n_out}"
            )

    except Exception as e:
        logger.error(e)
        if db_connection:
            db_connection.rollback()
    finally:
        if cur:
            cur.close()
        if db_connection:
            db_connection.close()


if __name__ == "__main__":
    args = parse_args()
    logger = get_and_set_logger(args.log_fname, args.verbose)
    main(args)
