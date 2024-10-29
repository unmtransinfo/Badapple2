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

        # Skip if assay not in custom selection
        if assay_ids and aid not in assay_ids:
            continue

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
    sql = """SELECT id FROM {DBSCHEMA}.scaffold ORDER BY id""".format(DBSCHEMA=dbschema)
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
):
    """For this scaffold, loop over compounds.  For each compound, loop over assay outcomes.
    Generate assay statistics.  Update scaffold row.
        cTotal  - compounds containing scaffold
        cTested - tested compounds containing scaffold
        cActive - active compounds containing scaffold
        sTotal  - substances containing scaffold
        sTested - tested substances containing scaffold
        sActive - active substances containing scaffold
        aTested - assays involving compounds containing scaffold
        aActive - assays involving active compounds containing scaffold
        wTested - samples (wells) involving compounds containing scaffold
        wActive - active samples (wells) involving compounds containing scaffold

    NOTE: This function presumes that the compound annotations have already been completed.
    """
    cTotal = 0  # total compounds, this scaffold
    cTested = 0  # compounds tested, this scaffold
    cActive = 0  # compounds active, this scaffold
    sTotal = 0  # total substances, this scaffold
    sTested = 0  # substances tested, this scaffold
    sActive = 0  # substances active, this scaffold
    aTested = 0  # assays tested, this scaffold
    aActive = 0  # assays active, this scaffold
    wTested = 0  # wells (samples) tested, this scaffold
    wActive = 0  # wells (samples) active, this scaffold
    nres_total = 0  # total results (outcomes) processed, this scaffold
    ok_write = False  # flag true if write row update ok
    n_err = 0

    # Fetch all relevant data in one query
    sql = f"""
    SELECT c.cid, c.nsub_total, c.nsub_tested, c.nsub_active, c.nass_tested, c.nass_active, c.nsam_tested, c.nsam_active,
           s2c.sid, a.{assay_id_tag}, a.outcome
    FROM {dbschema}.compound c
    JOIN {dbschema}.scaf2cpd sc ON sc.cid = c.cid
    JOIN {dbschema}.sub2cpd s2c ON s2c.cid = c.cid
    LEFT JOIN {dbschema_activity}.activity a ON a.sid = s2c.sid
    WHERE sc.scafid = %s
    """

    cur = db.cursor()
    cur.execute(sql, (scaf_id,))

    assays = set()
    compound_data = {}
    nres_total = 0  # Count total results processed

    for row in cur.fetchall():
        (
            cid,
            nsub_total,
            nsub_tested,
            nsub_active,
            nass_tested,
            nass_active,
            nsam_tested,
            nsam_active,
            sid,
            aid,
            outcome,
        ) = row

        if cid not in compound_data:
            compound_data[cid] = {
                "nsub_total": nsub_total or 0,
                "nsub_tested": nsub_tested or 0,
                "nsub_active": nsub_active or 0,
                "nass_tested": nass_tested or 0,
                "nass_active": nass_active or 0,
                "nsam_tested": nsam_tested or 0,
                "nsam_active": nsam_active or 0,
                "assays": set(),
                "is_tested": False,
                "is_active": False,
            }

        if aid is not None and (not assay_ids or aid in assay_ids):
            nres_total += 1
            compound_data[cid]["assays"].add((aid, outcome))
            if outcome in (2, 5):  # active or probe
                assays.add(aid)
                compound_data[cid]["is_active"] = True
            if outcome in (
                1,
                2,
                3,
                5,
            ):  # tested (inactive, active, inconclusive, probe)
                compound_data[cid]["is_tested"] = True

    # Process the collected data
    cTotal = len(compound_data)
    cTested = sum(1 for data in compound_data.values() if data["is_tested"])
    cActive = sum(1 for data in compound_data.values() if data["is_active"])
    sTotal = sum(data["nsub_total"] for data in compound_data.values())
    sTested = sum(data["nsub_tested"] for data in compound_data.values())
    sActive = sum(data["nsub_active"] for data in compound_data.values())
    wTested = sum(data["nsam_tested"] for data in compound_data.values())
    wActive = sum(data["nsam_active"] for data in compound_data.values())
    aTested = len({aid for data in compound_data.values() for aid, _ in data["assays"]})
    aActive = len(assays)

    # update scaffold row ...
    sql = f"""
    UPDATE {dbschema}.scaffold
    SET
        ncpd_total = {cTotal},
        ncpd_tested = {cTested},
        ncpd_active = {cActive},
        nsub_total = {sTotal},
        nsub_tested = {sTested},
        nsub_active = {sActive},
        nass_tested = {aTested},
        nass_active = {aActive},
        nsam_tested = {wTested},
        nsam_active = {wActive}
    WHERE
        id = {scaf_id}
    """

    if not no_write:
        try:
            cur1 = db.cursor()
            cur1.execute(sql)
            db.commit()
            cur1.close()
            ok_write = True
        except Exception as e:
            logger.error(e)
            n_err += 1

    return (
        nres_total,
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
    # (Implement any specific logic to fetch assay_ids if necessary)

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
            )
        )

        # Print summary
        logger.info(
            f"Scaffolds annotated: {n_scaf_total} ({n_cpd_total} compounds, {n_sub_total} substances, {n_res_total} results), {n_write} rows updated"
        )
        if n_err > 0:
            logger.info(f"Errors encountered: {n_err}")


if __name__ == "__main__":
    args = parse_arguments()
    logger = get_and_set_logger(args.log_fname, args.verbose)
    main(args)
