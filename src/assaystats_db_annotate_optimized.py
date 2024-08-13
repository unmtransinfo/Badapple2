"""
@author: Jeremy Yang, Jack Ringer
Date: 8/8/2024
Description: (Based on: https://github.com/unmtransinfo/Badapple/blob/master/python/badapple_assaystats_db_annotate.py)
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

from utils.logging import get_and_set_logger


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
    verbose=0,
):
    """Loop over compounds. For each compound call AnnotateCompound()."""
    n_cpd_total = 0  # total compounds processed
    n_sub_total = 0  # total substances processed
    n_res_total = 0  # total results (outcomes) processed
    n_write = 0  # total table rows modified
    n_err = 0
    cur = db.cursor()
    sql = f"SELECT cid FROM {dbschema}.compound"
    # if verbose > 2: print(f"DEBUG: sql=\"{sql}\"", file=sys.stderr)
    cur.execute(sql)
    cpd_rowcount = cur.rowcount  # use for progress msgs
    if verbose > 2:
        print(f"cpd rowcount={cpd_rowcount}", file=sys.stderr)
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
        if verbose > 2:
            print(f"CID={cid:4d}:", end=" ", file=sys.stderr)
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
            verbose,
        )
        n_sub_total += sTotal
        n_res_total += wTested
        if ok_write:
            n_write += 1
        n_err += n_err_this
        if (verbose > 0 and (n % 1000) == 0) or verbose > 2:
            print(
                f"n_cpd: {n_cpd_total} ; elapsed time: {time.time() - t0} ({100.0 * n_cpd_total / cpd_rowcount:.1f}% done)",
                file=sys.stderr,
            )
        row = cur.fetchone()
        if n_cpd_total == n_max:
            break
    cur.close()
    db.close()
    return n_cpd_total, n_sub_total, n_res_total, n_write, n_err


#############################################################################
def AnnotateCompound(
    cid, db, dbschema, dbschema_activity, assay_id_tag, assay_ids, no_write, verbose=0
):
    """Annotate compound with assay statistics."""

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
    assays = set()

    for sid, aid, outcome in cur.fetchall():
        if sid not in substances:
            substances[sid] = {"tested": False, "active": False, "assays": set()}

        if aid is not None:
            substances[sid]["tested"] = True
            if not assay_ids or aid in assay_ids:
                substances[sid]["assays"].add((aid, outcome))
                if outcome in (2, 5):  # active or probe
                    substances[sid]["active"] = True
                    assays.add(aid)

    cur.close()

    # Calculate statistics
    sTotal = len(substances)
    sTested = sum(1 for s in substances.values() if s["tested"])
    sActive = sum(1 for s in substances.values() if s["active"])
    aTested = len({aid for s in substances.values() for aid, _ in s["assays"]})
    aActive = len(assays)
    wTested = sum(len(s["assays"]) for s in substances.values())
    wActive = sum(
        sum(1 for _, outcome in s["assays"] if outcome in (2, 5))
        for s in substances.values()
    )

    # Update compound row
    if not no_write:
        sql = f"""
        UPDATE {dbschema}.compound
        SET nsub_total = %s, nsub_tested = %s, nsub_active = %s,
            nass_tested = %s, nass_active = %s, nsam_tested = %s, nsam_active = %s
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
            print(e, file=sys.stderr)
            ok_write = False
            n_err = 1
    else:
        ok_write = False
        n_err = 0

    if verbose > 1:
        print(
            f"CID={cid}, sTotal={sTotal}, sTested={sTested}, sActive={sActive}, "
            f"aTested={aTested}, aActive={aActive}, wTested={wTested}, wActive={wActive}",
            file=sys.stderr,
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
    verbose=0,
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
    if verbose > 2:
        print("\tscaf rowcount={}".format(scaf_rowcount), file=sys.stderr)
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
        if verbose > 2:
            print("SCAFID={:4d}:".format(scaf_id), file=sys.stderr)
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
            verbose,
        )
        n_cpd_total += cTotal
        n_sub_total += sTotal
        n_res_total += nres_this
        if ok_write:
            n_write += 1
        n_err += n_err_this
        if (verbose > 0 and (n % 100) == 0) or verbose > 2:
            print(
                "n_scaf: {} ; elapsed time: {} ({:.1f}% done)".format(
                    n_scaf_total,
                    time.strftime("%H:%M:%S", time.gmtime(time.time() - t0)),
                    100.0 * n_scaf_total / scaf_rowcount,
                ),
                file=sys.stderr,
            )
        row = cur.fetchone()
        if n_scaf_total == n_max:
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
    verbose=0,
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
           s.sid, a.{assay_id_tag}, a.outcome
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
                "nsub_total": nsub_total,
                "nsub_tested": nsub_tested,
                "nsub_active": nsub_active,
                "nass_tested": nass_tested,
                "nass_active": nass_active,
                "nsam_tested": nsam_tested,
                "nsam_active": nsam_active,
                "assays": set(),
            }

        if aid is not None and (not assay_ids or aid in assay_ids):
            compound_data[cid]["assays"].add((aid, outcome))
            if outcome in (2, 5):  # active or probe
                assays.add(aid)

    # Process the collected data
    cTotal = len(compound_data)
    cTested = sum(1 for data in compound_data.values() if data["nass_tested"] > 0)
    cActive = sum(1 for data in compound_data.values() if data["nass_active"] > 0)
    sTotal = sum(data["nsub_total"] or 0 for data in compound_data.values())
    sTested = sum(data["nsub_tested"] or 0 for data in compound_data.values())
    sActive = sum(data["nsub_active"] or 0 for data in compound_data.values())
    wTested = sum(data["nsam_tested"] or 0 for data in compound_data.values())
    wActive = sum(data["nsam_active"] or 0 for data in compound_data.values())
    aTested = len({aid for data in compound_data.values() for aid, _ in data["assays"]})
    aActive = len(assays)

    # update scaffold row ...
    sql = """
    UPDATE
        {DBSCHEMA}.scaffold
    SET
        ncpd_total = {NCPD_TOTAL},
        ncpd_tested = {NCPD_TESTED},
        ncpd_active = {NCPD_ACTIVE},
        nsub_total = {NSUB_TOTAL},
        nsub_tested = {NSUB_TESTED},
        nsub_active = {NSUB_ACTIVE},
        nass_tested = {NASS_TESTED},
        nass_active = {NASS_ACTIVE},
        nsam_tested = {NSAM_TESTED},
        nsam_active = {NSAM_ACTIVE}
    WHERE
        id={SCAFID}
    """.format(
        DBSCHEMA=dbschema,
        SCAFID=scaf_id,
        NCPD_TOTAL=cTotal,
        NCPD_TESTED=cTested,
        NCPD_ACTIVE=cActive,
        NSUB_TOTAL=sTotal,
        NSUB_TESTED=sTested,
        NSUB_ACTIVE=sActive,
        NASS_TESTED=aTested,
        NASS_ACTIVE=aActive,
        NSAM_TESTED=wTested,
        NSAM_ACTIVE=wActive,
    )
    if not no_write:
        try:
            cur1 = db.cursor()
            cur1.execute(sql)
            db.commit()
            cur1.close()
            ok_write = True
        except Exception as e:
            print(e, file=sys.stderr)
            n_err += 1
    if verbose > 1:
        print(
            "SCAFID={},cTotal={},cTested={},cActive={},sTotal={},sTested={},sActive={},aTested={},aActive={},wTested={},wActive={}".format(
                scaf_id,
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
            ),
            file=sys.stderr,
        )
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
        "-d",
        "--dbname",
        default="badapple2",
        help="Database name (default: %(default)s)",
    )
    parser.add_argument(
        "-s",
        "--schema",
        default="public",
        help="Database schema (default: %(default)s)",
    )
    parser.add_argument(
        "-a",
        "--activity",
        default="badapple",
        help="Activity schema (default: %(default)s)",
    )
    parser.add_argument(
        "-H", "--host", default="localhost", help="Database host (default: %(default)s)"
    )
    parser.add_argument(
        "-u",
        "--user",
        default=argparse.SUPPRESS,
        required=True,
        help="Database user",
    )
    parser.add_argument(
        "-p",
        "--pw",
        default=argparse.SUPPRESS,
        required=True,
        help="Database password",
    )
    parser.add_argument(
        "-n",
        "--nmax",
        type=int,
        default=0,
        help="Maximum number of records to process (default: %(default)s)",
    )
    parser.add_argument(
        "-x",
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
        "-w",
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
            password=args.pw,
            cursor_factory=psycopg2.extras.DictCursor,
        )
    except Exception as e:
        print(e, file=sys.stderr)
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
            args.verbose,
        )
        print(
            f"Compounds annotated: {n_cpd_total} ({n_sub_total} substances, {n_res_total} results), {n_write} rows updated"
        )
        if n_err > 0:
            print(f"Errors encountered: {n_err}")
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
                args.verbose,
            )
        )

        # Print summary
        print(
            f"Scaffolds annotated: {n_scaf_total} ({n_cpd_total} compounds, {n_sub_total} substances, {n_res_total} results), {n_write} rows updated"
        )
        if n_err > 0:
            print(f"Errors encountered: {n_err}")


if __name__ == "__main__":
    args = parse_arguments()
    logger = get_and_set_logger(args.log_fname)
    main(args)
