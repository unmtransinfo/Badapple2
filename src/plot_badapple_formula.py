"""
@author Jack Ringer
Date: 10/7/2024
Description:
Plot badapple formula using data from DB, based on:
https://github.com/unmtransinfo/Badapple/blob/master/R/badapple_formula.Rmd
"""

import argparse
import sys

import matplotlib.pyplot as plt
import psycopg2
import psycopg2.extras
from psycopg2.sql import SQL

from utils.custom_logging import get_and_set_logger


def parse_arguments(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--dbname",
        required=True,
        default=argparse.SUPPRESS,
        help="Database name",
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
        "--dbschema", default="public", help="Database schema (default: public)"
    )
    parser.add_argument(
        "--host", default="localhost", help="Database host (default: %(default)s)"
    )
    parser.add_argument("--plot_fname", default=None, help="File to save plot to.")
    parser.add_argument(
        "--log_fname",
        help="File to save logs to. If not given will log to stdout.",
        default=None,
    )
    return parser.parse_args()


def get_params(db_connection) -> dict:
    cursor = db_connection.cursor()
    queries = {
        "min_sTotal": "SELECT MIN(nsub_total) FROM scaffold;",
        "max_sTotal": "SELECT MAX(nsub_total) FROM scaffold;",
        "min_sTested": "SELECT MIN(nsub_tested) FROM scaffold;",
        "med_sTested": "SELECT median_nsub_tested FROM metadata;",
        "max_sTested": "SELECT MAX(nsub_tested) FROM scaffold;",
        "min_sActive": "SELECT MIN(nsub_active) FROM scaffold;",
        "med_sActive": "SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nsub_active) FROM scaffold;",
        "p80_sActive": "SELECT PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY nsub_active) FROM scaffold;",
        "max_sActive": "SELECT MAX(nsub_active) FROM scaffold;",
        "min_aTested": "SELECT MIN(nass_tested) FROM scaffold;",
        "med_aTested": "SELECT median_nass_tested FROM metadata;",
        "max_aTested": "SELECT MAX(nass_tested) FROM scaffold;",
        "min_aActive": "SELECT MIN(nass_active) FROM scaffold;",
        "med_aActive": "SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nass_active) FROM scaffold;",
        "max_aActive": "SELECT MAX(nass_active) FROM scaffold;",
        "min_wTested": "SELECT MIN(nsam_tested) FROM scaffold;",
        "med_wTested": "SELECT median_nsam_tested FROM metadata;",
        "max_wTested": "SELECT MAX(nsam_tested) FROM scaffold;",
        "min_wActive": "SELECT MIN(nsam_active) FROM scaffold;",
        "med_wActive": "SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nsam_active) FROM scaffold;",
        "p80_wActive": "SELECT PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY nsam_active) FROM scaffold;",
        "max_wActive": "SELECT MAX(nsam_active) FROM scaffold;",
    }

    params = {}
    for key, query in queries.items():
        cursor.execute(SQL(query))
        result = cursor.fetchone()
        params[key] = result[0] if result else None
    cursor.close()
    return params


def create_plot(db_connection, logger, plot_fname):
    params = get_params(db_connection)
    for key, value in params.items():
        logger.info(f"{key}: {int(value)}")

    p80_sActive = params["p80_sActive"]
    p80_wActive = params["p80_wActive"]
    xy_max = params["max_aTested"]
    z_mod = (
        100
        * (2 * params["med_sTested"])
        * (2 * params["med_wTested"])
        / p80_sActive
        / p80_wActive
        / 1e5
    )
    xy_mod_min = params["med_aTested"] * z_mod / (1 - z_mod)
    z_high = (
        300
        * (2 * params["med_sTested"])
        * (2 * params["med_wTested"])
        / p80_sActive
        / p80_wActive
        / 1e5
    )
    xy_high_min = params["med_aTested"] * z_high / (1 - z_high)
    y_low_max = z_mod * (xy_max + params["med_aTested"])
    y_mod_max = z_high * (xy_max + params["med_aTested"])

    # Data for plotting
    xLow = [0, xy_mod_min, xy_max]
    yLow = [0, xy_mod_min, y_low_max]
    xMod = [xy_mod_min, xy_high_min, xy_max]
    yMod = [xy_mod_min, xy_high_min, y_mod_max]
    xHigh = [xy_high_min, xy_max]
    yHigh = [xy_high_min, xy_max]

    # Create the plot
    plt.figure(figsize=(10, 8))

    # Plot in reverse order: green (back), yellow (middle), red (front)
    plt.fill_between(xHigh, yHigh, color="red", label="High [300,inf)")
    plt.fill_between(xMod, yMod, color="yellow", label="Moderate [100,300)")
    plt.fill_between(xLow, yLow, color="green", label="Low [0,100)")

    # Add lines on top for clear boundaries
    plt.plot(xHigh, yHigh, color="red", linewidth=2)
    plt.plot(xMod, yMod, color="yellow", linewidth=2)
    plt.plot(xLow, yLow, color="green", linewidth=2)

    plt.xlim(0, xy_max)
    plt.ylim(0, xy_max)
    plt.xlabel("Assays Tested")
    plt.ylabel("Assays Active")
    plt.title("Badapple scoring levels\nvs. assay active:tested ratio")
    leg = plt.legend(loc="upper left")
    p = leg.get_window_extent()

    # Add annotation
    annotate_str = "Substances Active (median, 80th percentile) = %d, %d\n" % (
        params["med_sActive"],
        p80_sActive,
    )
    annotate_str += "Samples Active (median, 80th percentile) = %d, %d\n" % (
        params["med_wActive"],
        p80_wActive,
    )
    annotate_str += "Assays Tested (median) = %d\n" % (params["med_aTested"])
    annotate_str += "Assays Active (median) = %d\n" % (params["med_aActive"])
    plt.annotate(
        annotate_str,
        xy=(p.p0[0] + 100, p.p1[1] + 60),
        xytext=(p.p0[0] + 100, p.p1[1] + 60),
        ha="left",
        va="center",
        fontsize=10,
    )

    plt.tight_layout()
    if plot_fname is not None:
        plt.savefig(plot_fname, dpi=300)
        logger.info(f"Saved plot to: {plot_fname}")
    plt.show()


def main(args):
    logger = get_and_set_logger(args.log_fname)
    try:
        db_conn = psycopg2.connect(
            dbname=args.dbname,
            host=args.host,
            user=args.user,
            password=args.password,
            cursor_factory=psycopg2.extras.DictCursor,
        )
    except Exception as e:
        logger.error(e)
        sys.exit(2)

    create_plot(db_conn, logger, args.plot_fname)
    db_conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a plot of the badapple formula based on data in given DB."
    )
    args = parse_arguments(parser)
    main(args)
