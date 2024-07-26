"""
@author Jack Ringer
Date: 7/26/2024
Description:
File-related utilities shared between multiple scripts.
"""

import csv
import sys


def get_csv_writer(file_path: str, delimiter: str):
    if file_path is sys.stdout:
        f = file_path
    else:
        f = open(file_path, "w")
    csv_writer = csv.writer(f, delimiter=delimiter)
    return csv_writer, f


def close_file(f):
    if f is not sys.stdout:
        f.close()
