"""
@author: Jeremy Yang, Jack Ringer
Date: 8/8/2024
Description: (Based on: https://github.com/unmtransinfo/Badapple/blob/master/python/badapple_annotate_db_assaystats.py)
After badapple database has been otherwise fully populated, with:
   -> compound table (id, nass_tested, nass_active, nsam_tested, nsam_active )
   -> scaffold table (id, ... )
   -> scaf2cpd table (scafid, cid )
   -> activity table (sid, aid, outcome )

Generate activity statistics and annotate compound and scaffold tables.

Optional: Selected assays for custom score, e.g. date or target criteria.

scaffold columns affected:
     ncpd_total, ncpd_tested, ncpd_active, nsub_total, nsub_tested, nsub_active, nass_tested, nass_active, nsam_tested, nsam_active

compound columns affected:
     nsub_total, nsub_tested, nsub_active, nass_tested, nass_active, nsam_tested, nsam_active

MLP Outcome codes:

   1 = inactive
   2 = active
   3 = inconclusive
   4 = unspecified
   5 = probe
   multiple, differing 1, 2 or 3 = discrepant
   not 4 = tested
"""

import argparse
import sys
import time

import psycopg2
import psycopg2.extras

from utils.custom_logging import get_and_set_logger
from utils.file_utils import read_aid_file


#############################################################################
def AnnotateCompounds(
    db,
    dbschema,
    dbschema_activity,
    assay_id_tag,
    assay_ids,
    no_write,
    n_max=0,
    n_skip=0,
):
    """Loop over compounds. For each compound call AnnotateCompound()."""
    n_cpd_total = 0  # total compounds processed
    n_sub_total = 0  # total substances processed
    n_res_total = 0  # total results (outcomes) processed
    n_write = 0  # total table rows modified
    n_err = 0
    cur = db.cursor()
    sql = f"SELECT cid FROM {dbschema}.compound"
    cur.execute(sql)
    cpd_rowcount = cur.rowcount  # use for progress msgs
    logger.debug(f"cpd rowcount={cpd_rowcount}")

    row = cur.fetchone()
    n = 0
    t0 = time.time()
    while row is not None:
        n += 1
        if n <= n_skip:
            row = cur.fetchone()
            continue
        n_cpd_total += 1
        cid = row[0]
        logger.debug(f"CID={cid:4d}:")

        (
            sTotal,
            sTested,
            sActive,
            aTested,
            aActive,
            wTested,
            wActive,
            ok_write,
            n_err_this,
        ) = AnnotateCompound(
            cid,
            db,
            dbschema,
            dbschema_activity,
            assay_id_tag,
            assay_ids,
            no_write,
        )
        n_sub_total += sTotal
        n_res_total += wTested
        if ok_write:
            n_write += 1
        n_err += n_err_this
        if (n % 1000) == 0:
            logger.info(
                f"n_cpd: {n_cpd_total} ; elapsed time: {time.time() - t0} ({100.0 * n_cpd_total / cpd_rowcount:.1f}% done)",
            )
        row = cur.fetchone()
        if n_max > 0 and n_cpd_total >= n_max:
            break
    cur.close()
    db.close()
    return n_cpd_total, n_sub_total, n_res_total, n_write, n_err


#############################################################################
def AnnotateCompound(
    cid, db, dbschema, dbschema_activity, assay_id_tag, assay_ids, no_write
):
    """Annotate compound with assay statistics.

    For this compound, loop over substances. For each substance, loop over assay outcomes.
    Generate assay statistics. Update compound row.
        sTotal  - substances containing scaffold
        sTested - tested substances containing scaffold
        sActive - active substances containing scaffold
        aTested - assays involving substances containing scaffold
        aActive - assays involving active substances containing scaffold
        wTested - samples (wells) involving substances containing scaffold
        wActive - active samples (wells) involving substances containing scaffold
    """
    # Fetch all relevant data in one query
    sql = f"""
    SELECT s.sid, a.{assay_id_tag}, a.outcome
    FROM {dbschema}.sub2cpd s
    LEFT JOIN {dbschema_activity}.activity a ON a.sid = s.sid
    WHERE s.cid = %s
    """

    cur = db.cursor()
    cur.execute(sql, (cid,))

    substances = {}
    assays = {}  # Using dict instead of set to match original behavior
    sTotal = 0
    sTested = 0
    sActive = 0
    wTested = 0
    wActive = 0

    # Group results by substance
    current_sid = None
    for sid, aid, outcome in cur.fetchall():
        # Skip if assay not in custom selection
        if assay_ids and aid not in assay_ids:
            continue

        # Count new substance
        if sid != current_sid:
            sTotal += 1
            current_sid = sid
            substances[sid] = {"tested": False, "active": False, "results": []}

        # Skip if no assay data
        if aid is None:
            continue

        # Mark substance as tested
        if not substances[sid]["tested"]:
            substances[sid]["tested"] = True
            sTested += 1

        # Count this well/sample
        wTested += 1
        substances[sid]["results"].append((aid, outcome))

        if outcome in (2, 5):  # active or probe
            wActive += 1
            if not substances[sid]["active"]:
                substances[sid]["active"] = True
                sActive += 1
            # Track active assay
            if aid in assays:
                assays[aid] = True
            else:
                assays[aid] = True
        elif outcome in (1, 3):  # tested inactive
            # Track tested but inactive assay
            if aid not in assays:
                assays[aid] = False

    cur.close()

    # Calculate assay statistics
    aTested = len(assays)
    aActive = sum(1 for active in assays.values() if active)

    # Update compound row
    ok_write = False
    n_err = 0

    if not no_write:
        sql = f"""
        UPDATE {dbschema}.compound
        SET 
            nsub_total = %s,
            nsub_tested = %s,
            nsub_active = %s,
            nass_tested = %s,
            nass_active = %s,
            nsam_tested = %s,
            nsam_active = %s
        WHERE cid = %s
        """
        try:
            cur = db.cursor()
            cur.execute(
                sql, (sTotal, sTested, sActive, aTested, aActive, wTested, wActive, cid)
            )
            db.commit()
            cur.close()
            ok_write = True
        except Exception as e:
            logger.error(e)
            n_err = 1

    logger.debug(
        f"CID={cid}, sTotal={sTotal}, sTested={sTested}, sActive={sActive}, "
        f"aTested={aTested}, aActive={aActive}, wTested={wTested}, wActive={wActive}"
    )

    return sTotal, sTested, sActive, aTested, aActive, wTested, wActive, ok_write, n_err


#############################################################################
def AnnotateScaffolds(
    db,
    dbschema,
    dbschema_activity,
    assay_id_tag,
    assay_ids,
    no_write,
    n_max=0,
    n_skip=0,
    write_scaf2activeaid=False,
    nass_tested_min: int = -1,
    scaffold_table: str = "scaffold",
):
    """Loop over scaffolds.  For each scaffold call AnnotateScaffold().
    NOTE: This function presumes that the compound annotations have already been accomplished
    by AnnotateCompounds().
    """
    n_scaf_total = 0  # total scaffolds processed
    n_cpd_total = 0  # total compounds processed
    n_sub_total = 0  # total substances processed
    n_res_total = 0  # total results (outcomes) processed
    n_write = 0  # total table rows modified
    n_err = 0

    cur = db.cursor()
    sql = """SELECT id FROM {DBSCHEMA}.{SCAFFOLD_TABLE} ORDER BY id""".format(
        SCAFFOLD_TABLE=scaffold_table, DBSCHEMA=dbschema
    )
    cur.execute(sql)
    scaf_rowcount = cur.rowcount  # use for progress msgs
    row = cur.fetchone()
    n = 0
    t0 = time.time()

    while row is not None:
        n += 1
        if n <= n_skip:
            row = cur.fetchone()
            continue
        n_scaf_total += 1
        scaf_id = row[0]
        logger.debug("SCAFID={:4d}:".format(scaf_id))
        (
            nres_this,
            cTotal,
            cTested,
            cActive,
            sTotal,
            sTested,
            sActive,
            aTested,
            aActive,
            wTested,
            wActive,
            ok_write,
            n_err_this,
        ) = AnnotateScaffold(
            scaf_id,
            db,
            dbschema,
            dbschema_activity,
            assay_id_tag,
            assay_ids,
            no_write,
            write_scaf2activeaid,
            nass_tested_min,
            scaffold_table,
        )
        n_cpd_total += cTotal
        n_sub_total += sTotal
        n_res_total += nres_this
        if ok_write:
            n_write += 1
        n_err += n_err_this
        if (n % 1000) == 0:
            logger.info(
                "n_scaf: {} ; elapsed time: {} ({:.1f}% done)".format(
                    n_scaf_total,
                    time.strftime("%H:%M:%S", time.gmtime(time.time() - t0)),
                    100.0 * n_scaf_total / scaf_rowcount,
                )
            )
        row = cur.fetchone()
        if n_max > 0 and n_scaf_total >= n_max:
            break
    cur.close()
    db.close()
    return n_scaf_total, n_cpd_total, n_sub_total, n_res_total, n_write, n_err


#############################################################################
def AnnotateScaffold(
    scaf_id,
    db,
    dbschema,
    dbschema_activity,
    assay_id_tag,
    assay_ids,
    no_write,
    write_scaf2activeaid: bool = False,
    nass_tested_min: int = -1,
    scaffold_table: str = "scaffold",
):
    """Annotate scaffold with assay statistics using aggregated SQL queries.

    Parameters:
    scaf_id (int): The ID of the scaffold to annotate
    db (cursor): Database connection
    dbschema (str): Name of the main database schema
    dbschema_activity (str): Name of the activity database schema
    assay_id_tag (str): The column name for the assay ID
    assay_ids (set or None): Optional set of assay IDs to filter on
    no_write (bool): If True, don't update the database
    write_scaf2activeaid (bool): If True and not(no_write), write updates to the scaf2activeaid table
    nass_tested_min (int): If > 0 then will only annotate stats from compounds which have been tested in >= nass_tested_min different assays
    scaffold_table (str): Table to be updated if no_write = False

    Returns:
    Tuple[int, int, int, int, int, int, int, int, int, int, int, bool, int]:
        nres_total, cTotal, cTested, cActive, sTotal, sTested, sActive,
        aTested, aActive, wTested, wActive, ok_write, n_err
    """
    n_err = 0
    ok_write = False

    # Prepare the assay IDs filter if provided
    assay_filter = ""
    if assay_ids:
        assay_ids_str = ",".join(map(str, assay_ids))
        assay_filter = f"AND a.{assay_id_tag} IN ({assay_ids_str})"

    # SQL query to aggregate counts
    sql = f"""
    WITH compound_data AS (
        SELECT
            c.cid,
            c.nsub_total,
            c.nsub_tested,
            c.nsub_active,
            c.nass_tested,
            c.nass_active,
            c.nsam_tested,
            c.nsam_active
        FROM {dbschema}.compound c
        JOIN {dbschema}.scaf2cpd sc ON sc.cid = c.cid
        WHERE sc.scafid = %s AND c.nass_tested >= %s
    ),
    activity_data AS (
        SELECT
            c.cid,
            a.{assay_id_tag} AS aid,
            a.outcome
        FROM compound_data c
        JOIN {dbschema}.sub2cpd s2c ON s2c.cid = c.cid
        LEFT JOIN {dbschema_activity}.activity a ON a.sid = s2c.sid
        WHERE a.{assay_id_tag} IS NOT NULL {assay_filter}
    ),
    counts AS (
        SELECT
            COUNT(DISTINCT c.cid) AS cTotal,
            SUM(c.nsub_total) AS sTotal,
            SUM(c.nsub_tested) AS sTested,
            SUM(c.nsub_active) AS sActive,
            SUM(c.nsam_tested) AS wTested,
            SUM(c.nsam_active) AS wActive
        FROM compound_data c
    ),
    tested_compounds AS (
        SELECT DISTINCT cid
        FROM activity_data
        WHERE outcome IN (1, 2, 3, 5)
    ),
    active_compounds AS (
        SELECT DISTINCT cid
        FROM activity_data
        WHERE outcome IN (2, 5)
    ),
    tested_assays AS (
        SELECT DISTINCT aid
        FROM activity_data
        WHERE outcome IN (1, 2, 3, 5)
    ),
    active_assays AS (
        SELECT DISTINCT aid
        FROM activity_data
        WHERE outcome IN (2, 5)
    ),
    all_compound_data AS (
        SELECT c.cid
        FROM {dbschema}.compound c
        JOIN {dbschema}.scaf2cpd sc ON sc.cid = c.cid
        WHERE sc.scafid = %s
    ),
    activity_data_all AS (
        SELECT
            c.cid,
            a.{assay_id_tag} AS aid,
            a.outcome
        FROM all_compound_data c
        JOIN {dbschema}.sub2cpd s2c ON s2c.cid = c.cid
        LEFT JOIN {dbschema_activity}.activity a ON a.sid = s2c.sid
        WHERE a.{assay_id_tag} IS NOT NULL {assay_filter}
    ),
    active_assays_all AS (
        SELECT DISTINCT aid
        FROM activity_data_all
        WHERE outcome IN (2, 5)
    ),
    total_results AS (
        SELECT COUNT(*) AS nres_total
        FROM activity_data
    )
    SELECT
        counts.cTotal,
        counts.sTotal,
        counts.sTested,
        counts.sActive,
        counts.wTested,
        counts.wActive,
        (SELECT COUNT(*) FROM tested_compounds),
        (SELECT COUNT(*) FROM active_compounds),
        (SELECT COUNT(*) FROM tested_assays),
        (SELECT COUNT(*) FROM active_assays),
        CASE WHEN %s THEN (SELECT array_agg(aid) FROM active_assays_all) ELSE NULL END,
        total_results.nres_total
    FROM counts, total_results
    """
    # for scaf2activeaid table we want to be inclusive - ok to include results from less-seen compounds
    include_unfiltered_active_assays = write_scaf2activeaid and nass_tested_min > 1
    params = (scaf_id, nass_tested_min, scaf_id, include_unfiltered_active_assays)
    cur = db.cursor()
    cur.execute(sql, params)
    result = cur.fetchone()
    cur.close()

    (
        cTotal,
        sTotal,
        sTested,
        sActive,
        wTested,
        wActive,
        cTested,
        cActive,
        aTested,
        aActive,
        activeAssayIDs,
        nres_total,
    ) = result

    # Update scaffold row
    update_sql = f"""
    UPDATE {dbschema}.{scaffold_table}
    SET
        ncpd_total = %s,
        ncpd_tested = %s,
        ncpd_active = %s,
        nsub_total = %s,
        nsub_tested = %s,
        nsub_active = %s,
        nass_tested = %s,
        nass_active = %s,
        nsam_tested = %s,
        nsam_active = %s
    WHERE
        id = %s
    """

    if not no_write:
        try:
            cur1 = db.cursor()
            cur1.execute(
                update_sql,
                (
                    cTotal or 0,
                    cTested or 0,
                    cActive or 0,
                    sTotal or 0,
                    sTested or 0,
                    sActive or 0,
                    aTested or 0,
                    aActive or 0,
                    wTested or 0,
                    wActive or 0,
                    scaf_id,
                ),
            )
            db.commit()
            cur1.close()
            ok_write = True
        except Exception as e:
            logger.error(e)
            n_err += 1

    if (
        ok_write
        and write_scaf2activeaid
        and activeAssayIDs is not None
        and len(activeAssayIDs) > 0
    ):
        try:
            cur1 = db.cursor()
            insert_query = "INSERT INTO scaf2activeaid (scafid, aid) VALUES (%s, %s)"
            data = [(scaf_id, aid) for aid in activeAssayIDs]
            cur1.executemany(insert_query, data)
            db.commit()
            cur1.close()
        except Exception as e:
            logger.error(e)
            n_err += 1

    return (
        nres_total or 0,
        cTotal or 0,
        cTested or 0,
        cActive or 0,
        sTotal or 0,
        sTested or 0,
        sActive or 0,
        aTested or 0,
        aActive or 0,
        wTested or 0,
        wActive or 0,
        ok_write,
        n_err,
    )


#############################################################################
# Define argument parser
def parse_arguments():
    # defaults
    parser = argparse.ArgumentParser(
        description="Annotate compounds and scaffolds in the database."
    )
    parser.add_argument(
        "--annotate_scaffolds",
        action="store_true",
        default=False,
        help="set to annotate scaffolds in the DB",
    )
    parser.add_argument(
        "--annotate_compounds",
        action="store_true",
        default=False,
        help="set to annotate compounds in the DB",
    )
    parser.add_argument(
        "--assay_id_tag", type=str, default="aid", help="assay ID column in the DB."
    )
    parser.add_argument(
        "--dbname",
        default="badapple2",
        help="Database name (default: %(default)s)",
    )
    parser.add_argument(
        "--schema",
        default="public",
        help="Database schema (default: %(default)s)",
    )
    parser.add_argument(
        "--activity",
        default="badapple",
        help="Activity schema (default: %(default)s)",
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
        "--nmax",
        type=int,
        default=0,
        help="Maximum number of records to process, if <=0 will process entire DB (default: %(default)s)",
    )
    parser.add_argument(
        "--nskip",
        type=int,
        default=0,
        help="Number of records to skip (default: %(default)s)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (use -vv for more verbose)",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Disable database writes (updates will be skipped)",
    )
    parser.add_argument(
        "--write_scafid2activeaid",
        action="store_true",
        help="Write to the scaf2activeaid table (Badapple2+ versions of DB)",
    )
    parser.add_argument(
        "--aid_file",
        type=str,
        default=None,
        help="(Optional) If given, will only annotate compounds/scaffolds using statistics from AssayIDs contained in the given file",
    )
    parser.add_argument(
        "--nass_tested_min",
        type=int,
        default=-1,
        help="(Optional) If given, will only annotate scaffold statistics using compounds which were tested in at least --nass_tested_min different assays (nass_tested >= --nass_tested_min assays)",
    )
    parser.add_argument(
        "--scaffold_table",
        type=str,
        default="scaffold",
        help="Name of scaffolds table. Included as an argument in case DB has multiple scaffold tables to test different configurations (e.g., different args to --nass_tested_min) ",
    )
    parser.add_argument(
        "--log_fname",
        help="File to save logs to. If not given will log to stdout.",
        default=None,
    )
    return parser.parse_args()


def main(args):
    # Connect to the database
    try:
        db = psycopg2.connect(
            dbname=args.dbname,
            host=args.host,
            user=args.user,
            password=args.password,
            cursor_factory=psycopg2.extras.DictCursor,
        )
    except Exception as e:
        logger.error(e)
        sys.exit(2)

    # Get the assay IDs if applicable
    assay_ids = None
    if args.aid_file is not None and len(args.aid_file) > 0 and args.aid_file != "NULL":
        logger.info(f"Will only annotate using AIDs from: {args.aid_file}")
        assay_ids = read_aid_file(args.aid_file)

    # Annotate compounds
    if args.annotate_compounds:
        n_cpd_total, n_sub_total, n_res_total, n_write, n_err = AnnotateCompounds(
            db,
            args.schema,
            args.activity,
            args.assay_id_tag,
            assay_ids,
            args.no_write,
            args.nmax,
            args.nskip,
        )
        logger.info(
            f"Compounds annotated: {n_cpd_total} ({n_sub_total} substances, {n_res_total} results), {n_write} rows updated"
        )
        if n_err > 0:
            logger.info(f"Errors encountered: {n_err}")

    # Annotate scaffolds
    if args.annotate_scaffolds:
        n_scaf_total, n_cpd_total, n_sub_total, n_res_total, n_write, n_err = (
            AnnotateScaffolds(
                db,
                args.schema,
                args.activity,
                args.assay_id_tag,
                assay_ids,
                args.no_write,
                args.nmax,
                args.nskip,
                args.write_scafid2activeaid,
                args.nass_tested_min,
                args.scaffold_table,
            )
        )

        logger.info(
            f"Scaffolds annotated: {n_scaf_total} ({n_cpd_total} compounds, {n_sub_total} substances, {n_res_total} results), {n_write} rows updated"
        )
        if n_err > 0:
            logger.info(f"Errors encountered: {n_err}")


if __name__ == "__main__":
    args = parse_arguments()
    logger = get_and_set_logger(args.log_fname, args.verbose)
    main(args)
