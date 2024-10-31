"""
@author Jack Ringer
Date: 8/26/2024
Description:
Annotate scaffold scores in the DB using the Badapple formula.
"""

import argparse
import sys
from typing import Union

import psycopg2
import psycopg2.extras
from psycopg2.extensions import cursor as Psycopg2Cursor

from utils.custom_logging import get_and_set_logger


def get_medians(cursor: Psycopg2Cursor, schema: str) -> dict[str, int]:
    medians = {}
    sql = f"SELECT median_ncpd_tested, median_nsub_tested, median_nass_tested, median_nsam_tested FROM {schema}.metadata"

    cursor.execute(sql)
    result = cursor.fetchone()
    if result:
        medians["median_cTested"] = result[0]
        medians["median_sTested"] = result[1]
        medians["median_aTested"] = result[2]
        medians["median_wTested"] = result[3]
    else:
        logger.error("ERROR: Badapple medians not found in database.", file=sys.stderr)
        raise Exception("ERROR: Badapple medians not found in database.")

    return medians


def compute_score(
    sTested: int,
    sActive: int,
    aTested: int,
    aActive: int,
    wTested: int,
    wActive: int,
    median_sTested: float,
    median_aTested: float,
    median_wTested: float,
) -> Union[float, None]:
    if sTested == 0 or aTested == 0 or wTested == 0:
        return None  # None means no evidence

    pScore = (
        1.0
        * sActive
        / (sTested + median_sTested)
        * aActive
        / (aTested + median_aTested)
        * wActive
        / (wTested + median_wTested)
        * 100.0
        * 1000.0
    )
    pScore = round(pScore, 0)  # round to whole number, matches badapple
    return pScore


def annotate_scaffold_scores(
    db_connection,
    cursor: Psycopg2Cursor,
    schema: str,
    scafid_min: int,
    scafid_max: int,
    verbose: int,
) -> int:

    medians = get_medians(cursor, schema)
    if verbose > 0:
        for key, value in medians.items():
            logger.info(f"medians[{key}]: {value}")

    sql = f"""
    SELECT id, scafsmi, scaftree, ncpd_total, ncpd_tested, ncpd_active, 
           nsub_total, nsub_tested, nsub_active, nass_tested, nass_active, 
           nsam_tested, nsam_active, in_drug 
    FROM {schema}.scaffold 
    WHERE id >= %s AND id <= %s 
    ORDER BY id ASC
    """

    cursor.execute(sql, (scafid_min, scafid_max))
    rows = cursor.fetchall()

    n_scaf = 0
    n_update = 0
    n_null = 0
    n_zero = 0
    n_gtzero = 0

    updates = []
    for row in rows:
        scafid = row[0]
        sTested = row[7]
        sActive = row[8]
        aTested = row[9]
        aActive = row[10]
        wTested = row[11]
        wActive = row[12]

        pScore = compute_score(
            sTested,
            sActive,
            aTested,
            aActive,
            wTested,
            wActive,
            medians["median_sTested"],
            medians["median_aTested"],
            medians["median_wTested"],
        )

        if pScore is None:
            n_null += 1
        elif pScore == 0.0:
            n_zero += 1
        else:
            n_gtzero += 1

        if pScore is not None:
            updates.append((pScore, scafid))
            n_update += 1
        n_scaf += 1
        if verbose > 0 and (n_scaf % 1000) == 0:
            logger.info(
                f"n_scaf: {n_scaf} ({int(100 * n_scaf / (scafid_max - scafid_min + 1))}%)"
            )

    # execute updates in batch (better performance):
    logger.info("Committing changes..")
    update_sql = f"UPDATE {schema}.scaffold SET pscore = %s WHERE id = %s"
    cursor.executemany(update_sql, updates)
    db_connection.commit()

    if n_scaf == 0:
        logger.error("ERROR: annotate_scaffold_scores() data not found.")

    logger.info(
        f"scafid range: [{scafid_min}-{scafid_max}] ({scafid_max - scafid_min + 1})",
    )
    logger.info(f"n_scaf: {n_scaf}")
    logger.info(f"n_null: {n_null} ; n_zero: {n_zero} ; n_gtzero: {n_gtzero}")
    logger.info(f"n_update: {n_update} (scores updated in db)")
    return n_scaf


def get_min_max_scaf_id(cursor: Psycopg2Cursor, schema: str) -> tuple[int, int]:
    sql = f"SELECT MIN(id), MAX(id) FROM {schema}.scaffold"
    cursor.execute(sql)
    result = cursor.fetchone()
    scafid_min, scafid_max = result if result else (0, 0)
    return scafid_min, scafid_max


def parse_arguments():
    parser = argparse.ArgumentParser(description="Annotate scaffold scores in the DB.")
    parser.add_argument(
        "-d",
        "--dbname",
        default="badapple2",
        help="Database name (default: %(default)s)",
    )
    parser.add_argument(
        "--dbschema", default="public", help="Database schema (default: public)"
    )
    parser.add_argument(
        "--host", default="localhost", help="Database host (default: %(default)s)"
    )
    parser.add_argument(
        "--user",
        default=argparse.SUPPRESS,
        required=True,
        help="Database user",
    )
    parser.add_argument(
        "--password",
        default=argparse.SUPPRESS,
        required=True,
        help="Database password",
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
    try:
        db_connection = psycopg2.connect(
            dbname=args.dbname,
            host=args.host,
            user=args.user,
            password=args.password,
            cursor_factory=psycopg2.extras.DictCursor,
        )
        cursor = db_connection.cursor()
    except Exception as e:
        logger.error(e)
        sys.exit(2)
    try:
        scafid_min, scafid_max = get_min_max_scaf_id(cursor, args.dbschema)
        n_scaf_done = annotate_scaffold_scores(
            db_connection,
            cursor,
            args.dbschema,
            scafid_min,
            scafid_max,
            args.verbose,
        )
        logger.info(f"scafs processed: {n_scaf_done}")
    finally:
        cursor.close()
        db_connection.close()


if __name__ == "__main__":
    args = parse_arguments()
    logger = get_and_set_logger(args.log_fname)
    main(args)
