"""
@author Jack Ringer
Date: 11/2024
Description:
Shared helper functions for Snakemake workflows.
"""

import os

ALREADY_UPDATED = False


def update_config_paths(config: dict):
    """
    Update config with full paths and other misc files.
    """
    global ALREADY_UPDATED
    if ALREADY_UPDATED:
        return  # no point in updating config over and over again

    # for assay list
    config["ASSAY_ID_FILE_PATH"] = os.path.join(
        config["ASSAY_DATA_DIR"], config["ASSAY_ID_FILE"]
    )
    config["BIOASSAY_FILE"] = os.path.join(
        config["LOCAL_PUBCHEM_DIR"], "Bioassay", "Extras", "bioassays.tsv.gz"
    )
    config["MIRROR_PUBCHEM_DONE_FILE"] = "logs/mirror_pubchem_records/job_done.txt"

    # for assay bioactivity data
    config["PUBCHEM_ASSAY_RECORDS_DIR"] = os.path.join(
        config["LOCAL_PUBCHEM_DIR"], "Bioassay", "CSV", "Data"
    )

    # save misc assay data to assay dir, db tables to base dir
    for key in list(config.keys()):
        if key.startswith("ASSAY") and key != "ASSAY_DATA_DIR":
            config[key + "_PATH"] = os.path.join(config["ASSAY_DATA_DIR"], config[key])
        elif key.endswith("TSV") and not (key.startswith("DRUG_CENTRAL")):
            config[key + "_PATH"] = os.path.join(config["BASE_DATA_DIR"], config[key])

    # save downloaded PubChem file to PubChem dir
    config["PUBCHEM_DATASOURCES_CSV_PATH"] = os.path.join(
        config["LOCAL_PUBCHEM_DIR"], config["PUBCHEM_DATASOURCES_CSV"]
    )
    # save downloaded DrugCentral file to designated dir
    config["DRUG_CENTRAL_TSV_PATH"] = os.path.join(
        config["DRUG_CENTRAL_DIR"], config["DRUG_CENTRAL_TSV"]
    )
