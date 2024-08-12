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
                if aid in assays:
                    assays[aid] = True
                else:
                    assays[aid] = True
                    nass_sub_this += 1
                    nass_sub_act_this += 1
            elif outcome in (1, 3):  # tested inactive
                if aid in assays:
                    assays[aid] |= False
                else:
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

    sql = """
    SELECT
        compound.cid,
        compound.nsub_total,
        compound.nsub_tested,
        compound.nsub_active,
        compound.nass_tested,
        compound.nass_active,
        compound.nsam_tested,
        compound.nsam_active
    FROM
        {DBSCHEMA}.compound,
        {DBSCHEMA}.scaf2cpd
    WHERE
        {DBSCHEMA}.scaf2cpd.scafid={SCAFID}
        AND {DBSCHEMA}.scaf2cpd.cid={DBSCHEMA}.compound.cid
    """.format(
        DBSCHEMA=dbschema, SCAFID=scaf_id
    )

    cur1 = db.cursor()
    cur1.execute(sql)
    cpd_rowcount = cur1.rowcount
    if verbose > 2:
        print("\tcpd rowcount={}".format(cpd_rowcount), file=sys.stderr)
    row1 = cur1.fetchone()
    assays = {}  # store unique assays for this scaffold

    while row1 is not None:  # compound loop
        (
            cid,
            c_sTotal,
            c_sTested,
            c_sActive,
            c_aTested,
            c_aActive,
            c_wTested,
            c_wActive,
        ) = row1
        cTotal += 1
        if c_aTested > 0:
            cTested += 1
        if c_aActive > 0:
            cActive += 1
        sTotal += c_sTotal if c_sTotal else 0
        sTested += c_sTested if c_sTested else 0
        sActive += c_sActive if c_sActive else 0
        wTested += c_wTested if c_wTested else 0
        wActive += c_wActive if c_wActive else 0

        ## Compound statistics are used to derive sTotal,sTested, sActive, wTested, and wActive.
        ## However we cannot use the compound statistics to derive aTested and aActive
        ## because we want to count assays per scaffold. So, for example, 2 compounds
        ## (with this scaffold) active in the same assay should increment aActive by only 1, not 2.

        # Now get substances...
        sql = """
        SELECT DISTINCT sid FROM {DBSCHEMA}.sub2cpd WHERE {DBSCHEMA}.sub2cpd.cid={CID}
        """.format(
            DBSCHEMA=dbschema, CID=cid
        )
        cur2 = db.cursor()
        cur2.execute(sql)
        sub_rowcount = cur2.rowcount
        if verbose > 2:
            print("\tsub rowcount={}".format(sub_rowcount), file=sys.stderr)
        row2 = cur2.fetchone()
        nres_cpd_this = 0  # outcome count, this compound
        nres_cpd_act_this = 0  # active outcome count, this compound
        nass_cpd_this = 0  # assay count, this compound
        nass_cpd_act_this = 0  # active assay count, this compound

        while row2 is not None:  # substance loop
            sid = row2[0]

            # Now get outcomes...
            sql = """
            SELECT
                activity.{ASSAY_ID_TAG}, activity.outcome
            FROM
                {DBSCHEMA_ACTIVITY}.activity
            WHERE
                {DBSCHEMA_ACTIVITY}.activity.sid={SID}
            """.format(
                ASSAY_ID_TAG=assay_id_tag, DBSCHEMA_ACTIVITY=dbschema_activity, SID=sid
            )
            t0 = time.time()
            cur3 = db.cursor()
            cur3.execute(sql)
            res_rowcount = cur3.rowcount
            if verbose > 2:
                print("\toutcome rowcount={}".format(res_rowcount), file=sys.stderr)
            row3 = cur3.fetchone()
            if row3 is None:  # No outcomes; normal, untested substance.
                row2 = cur2.fetchone()
                continue
            while row3 is not None:  # outcome loop
                aid, outcome = row3
                if assay_ids and (aid not in assay_ids):  # custom selection
                    row3 = cur3.fetchone()
                    continue
                nres_total += 1
                nres_cpd_this += 1
                if outcome in (2, 5):  # active or probe
                    nres_cpd_act_this += 1
                    if aid in assays:
                        assays[aid] = True
                    else:
                        assays[aid] = True
                        nass_cpd_this += 1
                        nass_cpd_act_this += 1
                elif outcome in (1, 3):  # tested inactive
                    if aid in assays:
                        assays[aid] |= False
                    else:
                        assays[aid] = False
                        nass_cpd_this += 1
                row3 = cur3.fetchone()  # END of outcome loop
            cur3.close()
            row2 = cur2.fetchone()  # END of substance loop
        cur2.close()
        if verbose > 2:
            print(
                "\t{:4d}. CID={:4d} n_res: {:4d} ; n_res_act: {:4d} ; n_ass: {:4d} ; n_ass_act: {:4d}".format(
                    cTotal,
                    cid,
                    nres_cpd_this,
                    nres_cpd_act_this,
                    nass_cpd_this,
                    nass_cpd_act_this,
                ),
                file=sys.stderr,
            )
            print(
                "\tcpd elapsed time: {} ({:.1f}% done this scaf)".format(
                    time.strftime("%H:%M:%S", time.gmtime(time.time() - t0)),
                    100.0 * cTotal / cpd_rowcount,
                ),
                file=sys.stderr,
            )
        row1 = cur1.fetchone()  # END of compound loop
    cur1.close()
    if verbose > 2:
        print(
            "\tn_cpd: {:4d} ; n_ass: {:4d}".format(cTotal, len(assays)), file=sys.stderr
        )
    for aid in assays.keys():
        aTested += 1
        if assays[aid]:
            aActive += 1

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
