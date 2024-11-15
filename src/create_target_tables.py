"""
@author Jack Ringer
Date: 11/15/2024
Description:
Script which generates the TSVs used to populate the "target" and "aid2target"
tables in the badapple2 DB. Uses output of gather_protein_families.py
Will assign target_id to each unique target in input (requires combining duplicates). 
"""

import pandas as pd


def are_duplicates(row1, row2) -> bool:
    type_1, type_2 = row1["TargetType"], row2["TargetType"]
    if pd.isna(type_1) or pd.isna(type_2) or type_1 != type_2:
        return False
    elif type_1 in ["Protein", "Gene", "Nucleotide", "Pathway"]:
        pid_1, pid_2 = row1["PubChemID"], row2["PubChemID"]
        assert not (pd.isna(pid_1)), f"NaN PubChemID in row: {row1}"
        assert not (pd.isna(pid_2)), f"NaN PubChemID in row: {row2}"
        if type_1 == "Protein":
            uni_1, uni_2 = row1["UniProtID"], row2["UniProtID"]
            if (pid_1 == pid_2) and (uni_1 == uni_2):
                return True
            elif (pid_1 != pid_2) and (uni_1 != uni_2):
                return False
            raise ValueError(
                f"Inconsistent PubChemID-UniProtID pattern: {row1}, {row2}"
            )
        return pid_1 == pid_2
    raise ValueError(f"Unrecognized target type in row: {row1}")
