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

from utils.logging import get_and_set_logger

ASSAY_ID_TAG = "aid"


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
    """For this compound, loop over substances. For each substance, loop over assay outcomes.
    Generate assay statistics. Update compound row.
        sTotal    - substances containing scaffold
        sTested   - tested substances containing scaffold
        sActive   - active substances containing scaffold
        aTested   - assays involving substances containing scaffold
        aActive   - assays involving active substances containing scaffold
        wTested   - samples (wells) involving substances containing scaffold
        wActive   - active samples (wells) involving substances containing scaffold
    """
    sTotal = 0  # total substances, this compound
    sTested = 0  # substances tested, this compound
    sActive = 0  # substances active, this compound
    aTested = 0  # assays tested, this compound
    aActive = 0  # assays active, this compound
    wTested = 0  # wells (samples) tested, this compound
    wActive = 0  # wells (samples) active, this compound
    ok_write = False  # flag true if write row update ok
    n_err = 0
    sql = f"SELECT DISTINCT sid FROM {dbschema}.sub2cpd WHERE {dbschema}.sub2cpd.cid=%s"
    cur1 = db.cursor()
    # if verbose > 2: print(f"DEBUG: sql=\"{sql}\"", file=sys.stderr)
    cur1.execute(sql, (cid,))
    sub_rowcount = cur1.rowcount
    if verbose > 2:
        print(f"sub rowcount={sub_rowcount}", file=sys.stderr)
    row1 = cur1.fetchone()
    assays = {}  # store unique assays for this compound
    while row1 is not None:  # substance loop
        sid = row1[0]
        sTotal += 1

        # Now get outcomes...
        sql = f"""
        SELECT
            {assay_id_tag}, outcome
        FROM
            {dbschema_activity}.activity
        WHERE
            {dbschema_activity}.activity.sid=%s
        """
        # if verbose > 2: print(f"DEBUG: sql=\"{sql}\"", file=sys.stderr)
        t0 = time.time()
        cur2 = db.cursor()
        cur2.execute(sql, (sid,))
        res_rowcount = cur2.rowcount
        # if verbose > 2: print(f"outcome rowcount={res_rowcount}", file=sys.stderr)
        row2 = cur2.fetchone()
        if row2 is None:  # no outcomes; not tested
            if verbose > 2:
                print(f'DEBUG: no outcomes; sql="{sql}"', file=sys.stderr)
            row1 = cur1.fetchone()
            continue
        sTested += 1
        nres_sub_this = 0
        nres_sub_act_this = 0
        nass_sub_this = 0
        nass_sub_act_this = 0
        while row2 is not None:  # outcome loop
            aid, outcome = row2
            if assay_ids and (aid not in assay_ids):  # custom selection
                row2 = cur2.fetchone()
                continue
            wTested += 1
            nres_sub_this += 1
            if outcome in (2, 5):  # active or probe
                nres_sub_act_this += 1
                wActive += 1
                assays[aid] = True
                nass_sub_this += 1
                nass_sub_act_this += 1
            elif outcome in (1, 3):  # tested inactive
                assays[aid] = False
                nass_sub_this += 1
            row2 = cur2.fetchone()
        cur2.close()
        row1 = cur1.fetchone()
        if nres_sub_act_this > 0:
            sActive += 1
        if verbose > 2:
            print(
                f"\t{sTested:4d}. SID={sid:4d} n_res: {nres_sub_this:4d} ; n_res_act: {nres_sub_act_this:4d} ; n_ass: {nass_sub_this:4d} ; n_ass_act: {nass_sub_act_this:4d}",
                file=sys.stderr,
            )
    cur1.close()
    if verbose > 2:
        print(f"n_sub: {sTested:4d} ; n_ass: {len(assays):4d}", file=sys.stderr)
    for aid in assays.keys():
        aTested += 1
        if assays[aid]:
            aActive += 1

    # update compound row ...
    sql = f"""
    UPDATE
        {dbschema}.compound
    SET
        nsub_total = %s,
        nsub_tested = %s,
        nsub_active = %s,
        nass_tested = %s,
        nass_active = %s,
        nsam_tested = %s,
        nsam_active = %s
    WHERE
        cid=%s
    """
    if not no_write:
        try:
            cur1 = db.cursor()
            cur1.execute(
                sql, (sTotal, sTested, sActive, aTested, aActive, wTested, wActive, cid)
            )
            db.commit()
            cur1.close()
            ok_write = True
        except Exception as e:
            print(e, file=sys.stderr)
            n_err += 1
    if verbose > 1:
        print(
            f"CID={cid}, sTotal={sTotal}, sTested={sTested}, sActive={sActive}, aTested={aTested}, aActive={aActive}, wTested={wTested}, wActive={wActive}",
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
    """Loop over scaffolds. For each scaffold call AnnotateScaffold().
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
    sql = f"SELECT scaf_id FROM {dbschema}.scaffold"
    # if verbose > 2: print(f"DEBUG: sql=\"{sql}\"", file=sys.stderr)
    cur.execute(sql)
    scaf_rowcount = cur.rowcount  # use for progress msgs
    if verbose > 2:
        print(f"scaf rowcount={scaf_rowcount}", file=sys.stderr)
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
            print(f"Scaffold={scaf_id:4d}:", end=" ", file=sys.stderr)
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
        n_cpd_total += sTotal
        n_sub_total += sTested
        n_res_total += wTested
        if ok_write:
            n_write += 1
        n_err += n_err_this
        if (verbose > 0 and (n % 1000) == 0) or verbose > 2:
            print(
                f"n_scaf: {n_scaf_total} ; elapsed time: {time.time() - t0} ({100.0 * n_scaf_total / scaf_rowcount:.1f}% done)",
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
    """For this scaffold, loop over compounds. For each compound, loop over substances.
    Generate scaffold statistics. Update scaffold row.
        sTotal    - compounds containing scaffold
        sTested   - tested compounds containing scaffold
        sActive   - active compounds containing scaffold
        aTested   - assays involving compounds containing scaffold
        aActive   - assays involving active compounds containing scaffold
        wTested   - samples (wells) involving compounds containing scaffold
        wActive   - active samples (wells) involving compounds containing scaffold
    """
    sTotal = 0  # total compounds, this scaffold
    sTested = 0  # compounds tested, this scaffold
    sActive = 0  # compounds active, this scaffold
    aTested = 0  # assays tested, this scaffold
    aActive = 0  # assays active, this scaffold
    wTested = 0  # wells (samples) tested, this scaffold
    wActive = 0  # wells (samples) active, this scaffold
    ok_write = False  # flag true if write row update ok
    n_err = 0
    sql = f"SELECT DISTINCT cid FROM {dbschema}.sub2scaf WHERE {dbschema}.sub2scaf.scaf_id=%s"
    cur1 = db.cursor()
    # if verbose > 2: print(f"DEBUG: sql=\"{sql}\"", file=sys.stderr)
    cur1.execute(sql, (scaf_id,))
    cpd_rowcount = cur1.rowcount
    if verbose > 2:
        print(f"cpd rowcount={cpd_rowcount}", file=sys.stderr)
    row1 = cur1.fetchone()
    assays = {}  # store unique assays for this scaffold
    while row1 is not None:  # compound loop
        cid = row1[0]
        sTotal += 1
        (
            sTotal_cpd,
            sTested_cpd,
            sActive_cpd,
            aTested_cpd,
            aActive_cpd,
            wTested_cpd,
            wActive_cpd,
            ok_write_cpd,
            n_err_cpd,
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
        sTested += sTested_cpd
        sActive += sActive_cpd
        aTested += aTested_cpd
        aActive += aActive_cpd
        wTested += wTested_cpd
        wActive += wActive_cpd
        if ok_write_cpd:
            ok_write = True
        n_err += n_err_cpd
        row1 = cur1.fetchone()
    cur1.close()
    # update scaffold row ...
    sql = f"""
    UPDATE
        {dbschema}.scaffold
    SET
        ncpd_total = %s,
        ncpd_tested = %s,
        ncpd_active = %s,
        nass_tested = %s,
        nass_active = %s,
        nsam_tested = %s,
        nsam_active = %s
    WHERE
        scaf_id=%s
    """
    if not no_write:
        try:
            cur1 = db.cursor()
            cur1.execute(
                sql,
                (sTotal, sTested, sActive, aTested, aActive, wTested, wActive, scaf_id),
            )
            db.commit()
            cur1.close()
            ok_write = True
        except Exception as e:
            print(e, file=sys.stderr)
            n_err += 1
    if verbose > 1:
        print(
            f"Scaffold={scaf_id}, sTotal={sTotal}, sTested={sTested}, sActive={sActive}, aTested={aTested}, aActive={aActive}, wTested={wTested}, wActive={wActive}",
            file=sys.stderr,
        )

    return sTotal, sTested, sActive, aTested, aActive, wTested, wActive, ok_write, n_err


#############################################################################
# Define argument parser
def parse_arguments():
    # defaults
    parser = argparse.ArgumentParser(
        description="Annotate compounds and scaffolds in the database."
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
            dbname=args.dbname, host=args.host, user=args.user, password=args.pw
        )
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(2)

    # Get the assay IDs if applicable
    assay_ids = None
    # (Implement any specific logic to fetch assay_ids if necessary)

    # Annotate compounds and scaffolds
    n_cpd_total, n_sub_total, n_res_total, n_write, n_err = AnnotateCompounds(
        db,
        args.schema,
        args.activity,
        ASSAY_ID_TAG,
        assay_ids,
        args.no_write,
        args.nmax,
        args.nskip,
        args.verbose,
    )
    n_scaf_total, n_cpd_total, n_sub_total, n_res_total, n_write, n_err = (
        AnnotateScaffolds(
            db,
            args.schema,
            args.activity,
            ASSAY_ID_TAG,
            assay_ids,
            args.no_write,
            args.nmax,
            args.nskip,
            args.verbose,
        )
    )

    # Print summary
    print(
        f"Compounds annotated: {n_cpd_total} ({n_sub_total} substances, {n_res_total} results), {n_write} rows updated"
    )
    print(
        f"Scaffolds annotated: {n_scaf_total} ({n_cpd_total} compounds, {n_sub_total} substances, {n_res_total} results), {n_write} rows updated"
    )
    if n_err > 0:
        print(f"Errors encountered: {n_err}")


if __name__ == "__main__":
    args = parse_arguments()
    logger = get_and_set_logger(args.log_fname)
    main(args)
