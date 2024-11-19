"""
@author Jack Ringer
Date: 7/26/2024
Description:
File-related utilities shared between multiple scripts.
"""

import csv
import json
import sys


def load_json_file(json_file: str):
    data = {}
    with open(json_file, "r") as f:
        data = json.load(f)
    return data


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


def read_aid_file(aid_file_path: str) -> list[int]:
    with open(aid_file_path, "r") as file:
        aid_list = [int(line.strip()) for line in file if line.strip().isdigit()]
    return aid_list


def write_aid_file(aid_list: list, aid_file_path: str):
    aid_list = sorted([int(x) for x in set(aid_list)])
    with open(aid_file_path, "w") as f:
        for aid in aid_list:
            f.write(f"{aid}\n")
