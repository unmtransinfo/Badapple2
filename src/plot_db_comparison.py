"""
@author Jack Ringer
Date: 5/22/2025
Description:
Create several visualizations comparing pScores and other statistics between different Badapple DB versions.
Replicates some of the important analyses done in the comparison notebooks (e.g., badapple2-vs-badapple_classic.ipynb)
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psycopg2
import psycopg2.extras
import seaborn as sns
from psycopg2 import sql
from scipy.stats import pearsonr


def parse_arguments(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--save_dir",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="Directory to save figures to",
    )

    parser.add_argument(
        "--original_db_name",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="Original database name",
    )
    parser.add_argument(
        "--original_db_host",
        type=str,
        default="localhost",
        help="Original DB host",
    )
    parser.add_argument(
        "--original_db_user",
        type=str,
        default=argparse.SUPPRESS,
        required=True,
        help="Original DB user",
    )
    parser.add_argument(
        "--original_db_password",
        type=str,
        default=argparse.SUPPRESS,
        help="Original DB password",
    )
    parser.add_argument(
        "--original_db_port",
        type=int,
        default=5432,
        help="Original DB port (default: %(default)s)",
    )
    parser.add_argument(
        "--original_scaffold_table",
        type=str,
        default="scaffold",
        help="Name of scaffold table to draw pScores and other scaffold statistics from for original DB",
    )

    parser.add_argument(
        "--comparison_db_name",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="Comparison database name",
    )
    parser.add_argument(
        "--comparison_db_host",
        type=str,
        default="localhost",
        help="Comparison DB host",
    )
    parser.add_argument(
        "--comparison_db_user",
        type=str,
        default=argparse.SUPPRESS,
        required=True,
        help="Comparison DB user",
    )
    parser.add_argument(
        "--comparison_db_password",
        type=str,
        default=argparse.SUPPRESS,
        help="Comparison DB password",
    )
    parser.add_argument(
        "--comparison_db_port",
        type=int,
        default=5432,
        help="Comparison DB port (default: %(default)s)",
    )
    parser.add_argument(
        "--comparison_scaffold_table",
        type=str,
        default="scaffold",
        help="Name of scaffold table to draw pScores and other scaffold statistics from for comparison DB",
    )
    return parser.parse_args()


def db_connect(db_name: str, host: str, user: str, password: str, port: int = 5432):
    try:
        db_connection = psycopg2.connect(
            dbname=db_name,
            host=host,
            user=user,
            password=password,
            port=port,
            cursor_factory=psycopg2.extras.DictCursor,
        )
        db_connection.set_session(readonly=True)
        return db_connection
    except Exception as e:
        print(e)
        print(f"Error connecting to DB: {db_name}")
        return None


def get_pScores(db_cursor, db_conn, scaffold_table: str):
    query = sql.SQL(f"SELECT scafsmi, pScore FROM {scaffold_table} order by scafsmi")
    result = []
    try:
        db_cursor.execute(query)
        result = db_cursor.fetchall()
        return result
    except Exception:
        db_conn.rollback()
    return result


def get_pScore_df(pScore_list: list[list[str, int]], dropna: bool = True):
    df = pd.DataFrame(pScore_list, columns=["scafsmi", "pScore"])
    if dropna:
        # some compounds in badapple+badapple_classic have 'None' as pScore (no evidence)
        # this is because the compound list was from MLSMR, not from the set of compounds in the assays
        # drop these scores as it does not make sense to try and compare these NaN cases
        df.dropna(subset="pScore", inplace=True)
    return df


def create_parity_plot(
    df: pd.DataFrame, x_col: str, y_col: str, title: str, save_fname: str
):
    plt.style.use("ggplot")
    x, y = df[x_col], df[y_col]
    plt.scatter(x, y, alpha=0.5)
    # parity line
    min_val = min(np.minimum(x, y))
    max_val = max(np.maximum(x, y))
    plt.plot(
        [min_val, max_val],
        [min_val, max_val],
        "k",
        lw=2,
    )
    plt.axis("scaled")
    ax = plt.gca()
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    if title is not None:
        ax.set_title(title)
    plt.tight_layout()
    plt.savefig(save_fname, dpi=300)


def create_score_histogram(pScore_values: pd.Series, db_source: str, save_fname: str):
    # map NaN values to -1 for sake of plotting
    pScore_values.fillna(-1, inplace=True)
    # Define the ranges and corresponding colors
    ranges = [(-float("inf"), 0), (0, 100), (100, 300), (300, float("inf"))]
    colors = ["grey", "green", "yellow", "red"]
    labels = ["pScore = ~", "0 <= pScore < 100", "100 <= pScore < 300", "pScore >= 300"]

    # Create lists to hold the pScore values for each range
    pScore_lists = [[] for _ in ranges]
    counts = [0] * len(ranges)

    # Distribute the pScore values into the corresponding lists
    for pScore in pScore_values:
        for i, (low, high) in enumerate(ranges):
            if low <= pScore < high:
                pScore_lists[i].append(pScore)
                counts[i] += 1
                break

    # Define the bin edges in increments of 25
    bin_size = 25
    # min score is 0
    bin_edges = np.arange(-bin_size, max(pScore_values) + bin_size, bin_size)

    # Plot the histogram
    plt.figure(figsize=(10, 6))
    for pScore_list, color in zip(pScore_lists, colors):
        plt.hist(pScore_list, bins=bin_edges, color=color, edgecolor="black", alpha=0.7)

    plt.xlabel("pScore")
    plt.ylabel("Frequency")
    plt.yscale("log")
    plt.title(f"Histogram of pScore Values from {db_source}\nBin Size={bin_size}")

    total_count = len(pScore_values)
    pct = lambda count: "%.2f" % ((100 * count) / total_count)
    legend_labels = [
        f"{label} : {count} ({pct(count)}%)" for label, count in zip(labels, counts)
    ]
    legend_title = f"Counts (Total={total_count})"
    plt.legend(legend_labels, title=legend_title, loc="upper right")
    plt.tight_layout()
    plt.savefig(save_fname, dpi=300)


def classify_pScore(pScore):
    if pScore < 100:
        return "low"
    elif pScore < 300:
        return "moderate"
    else:
        return "high"


def create_score_heatmap(
    shared_df: pd.DataFrame,
    ORIGINAL_PSCORE_COL_NAME: str,
    COMPARISON_PSCORE_COL_NAME: str,
    ORIGINAL_DB_NAME: str,
    COMPARISON_DB_NAME: str,
    save_fname: str,
):
    shared_df["classic_class"] = shared_df[ORIGINAL_PSCORE_COL_NAME].apply(
        classify_pScore
    )
    shared_df["new_class"] = shared_df[COMPARISON_PSCORE_COL_NAME].apply(
        classify_pScore
    )

    # Create a column for transitions
    shared_df["transition"] = (
        shared_df["classic_class"] + " -> " + shared_df["new_class"]
    )
    desired_order = ["low", "moderate", "high"]
    transition_matrix = (
        shared_df.groupby(["new_class", "classic_class"]).size().unstack(fill_value=0)
    )
    transition_matrix = transition_matrix.reindex(
        index=desired_order, columns=desired_order
    )

    # Logarithmic transformation of the transition matrix
    log_transition_matrix = np.log1p(
        transition_matrix
    )  # log1p to handle zeros (log(1 + x))

    # Plot the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        log_transition_matrix,
        annot=transition_matrix,  # Show original counts as annotations
        fmt="d",
        cmap="Blues",
        cbar_kws={"label": "Frequency"},
        linewidths=0.5,
        square=True,
    )

    # Customize the colorbar ticks
    colorbar = plt.gca().collections[0].colorbar
    original_ticks = [0, 1, 10, 100, 1000, 10000, sum(transition_matrix.sum())]
    log_ticks = np.log1p(original_ticks)
    colorbar.set_ticks(log_ticks)
    colorbar.set_ticklabels(original_ticks)

    plt.title(f"pScore Transition Heatmap (Log Scale)", fontsize=14)
    plt.xlabel(f"{ORIGINAL_DB_NAME} Advisory", fontsize=12)
    plt.ylabel(f"{COMPARISON_DB_NAME} Advisory", fontsize=12)
    plt.tight_layout()
    plt.savefig(save_fname, dpi=300)


def main(args):
    save_dir = args.save_dir
    os.makedirs(save_dir, exist_ok=True)
    # connect to DBs
    ORIGINAL_DB_NAME = args.original_db_name
    ORIGINAL_DB_HOST = args.original_db_host
    ORIGINAL_DB_USER = args.original_db_user
    ORIGINAL_DB_PASSWORD = args.original_db_password
    ORIGINAL_DB_PORT = args.original_db_port

    COMPARISON_DB_NAME = args.comparison_db_name
    COMPARISON_DB_HOST = args.comparison_db_host
    COMPARISON_DB_USER = args.comparison_db_user
    COMPARISON_DB_PASSWORD = args.comparison_db_password
    COMPARISON_DB_PORT = args.comparison_db_port

    original_db_connection = db_connect(
        ORIGINAL_DB_NAME,
        ORIGINAL_DB_HOST,
        ORIGINAL_DB_USER,
        ORIGINAL_DB_PASSWORD,
        ORIGINAL_DB_PORT,
    )
    comparison_db_connection = db_connect(
        COMPARISON_DB_NAME,
        COMPARISON_DB_HOST,
        COMPARISON_DB_USER,
        COMPARISON_DB_PASSWORD,
        COMPARISON_DB_PORT,
    )
    original_db_cur = original_db_connection.cursor()
    comparison_db_cur = comparison_db_connection.cursor()

    # get pScores
    ORIGINAL_PSCORE_COL_NAME = f"pScore {ORIGINAL_DB_NAME}"
    COMPARISON_PSCORE_COL_NAME = f"pScore {COMPARISON_DB_NAME}"
    original_pScores = get_pScores(
        original_db_cur, original_db_connection, args.original_scaffold_table
    )
    comparison_pScores = get_pScores(
        comparison_db_cur, comparison_db_connection, args.comparison_scaffold_table
    )
    original_df = get_pScore_df(original_pScores, False)
    comparison_df = get_pScore_df(comparison_pScores, False)

    shared_df = pd.merge(original_df, comparison_df, on="scafsmi")
    shared_df.rename(
        columns={
            "pScore_x": ORIGINAL_PSCORE_COL_NAME,
            "pScore_y": COMPARISON_PSCORE_COL_NAME,
        },
        inplace=True,
    )
    # doesn't make sense to compare NaN entries
    shared_df = shared_df[
        ~(
            shared_df[ORIGINAL_PSCORE_COL_NAME].isna()
            | shared_df[COMPARISON_PSCORE_COL_NAME].isna()
        )
    ]

    # create parity plot
    correlation, p_value = pearsonr(
        shared_df[ORIGINAL_PSCORE_COL_NAME], shared_df[COMPARISON_PSCORE_COL_NAME]
    )
    plot_title = (
        f"{ORIGINAL_DB_NAME} vs {COMPARISON_DB_NAME} pScore Parity Plot\nr = %.3f, n_points= %d"
        % (correlation, len(shared_df))
    )
    create_parity_plot(
        shared_df,
        ORIGINAL_PSCORE_COL_NAME,
        COMPARISON_PSCORE_COL_NAME,
        plot_title,
        os.path.join(save_dir, "parity_plot.png"),
    )

    # create histograms of pScores
    create_score_histogram(
        original_df["pScore"],
        f"{ORIGINAL_DB_NAME}",
        os.path.join(save_dir, f"{ORIGINAL_DB_NAME}_pscore_histogram.png"),
    )
    create_score_histogram(
        comparison_df["pScore"],
        f"{COMPARISON_DB_NAME}",
        os.path.join(save_dir, f"{COMPARISON_DB_NAME}_pscore_histogram.png"),
    )
    create_score_histogram(
        shared_df[ORIGINAL_PSCORE_COL_NAME],
        f"{ORIGINAL_DB_NAME}",
        os.path.join(save_dir, f"{ORIGINAL_DB_NAME}_shared-scaf_pscore_histogram.png"),
    )
    create_score_histogram(
        shared_df[COMPARISON_PSCORE_COL_NAME],
        f"{COMPARISON_DB_NAME}",
        os.path.join(
            save_dir, f"{COMPARISON_DB_NAME}_shared-scaf_pscore_histogram.png"
        ),
    )

    # create heatmap
    create_score_heatmap(
        shared_df,
        ORIGINAL_PSCORE_COL_NAME,
        COMPARISON_PSCORE_COL_NAME,
        ORIGINAL_DB_NAME,
        COMPARISON_DB_NAME,
        os.path.join(save_dir, "score_heatmap.png"),
    )

    # Close the cursors
    original_db_cur.close()
    comparison_db_cur.close()

    # Close the connections
    original_db_connection.close()
    comparison_db_connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a parity plot, histograms, and heatmap comparing pScores between two Badapple DBs."
    )
    args = parse_arguments(parser)
    main(args)
