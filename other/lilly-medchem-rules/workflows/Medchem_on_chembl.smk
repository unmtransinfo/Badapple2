"""
@author Jack Ringer
Date: 3/24/2026
Description:
Snakemake workflow which:
1) Downloads a gz file containing the SMILES structures of all compounds in ChEMBL (version 35)
2) Analyzes the dataset using Medchem's implementation of Lilly demerits (https://github.com/datamol-io/medchem/tree/main/medchem/structural/lilly_demerits)
3) Saves the results to a TSV file
"""

from snakemake.utils import min_version

min_version("6.0")


configfile: "config.yaml"

rule all:
    input:
        config["lilly_demerits_tsv_file"],

# 1) Download gz file
rule download_chembl_file:
    output:
        config["chembl_smiles_gz_file"],
    log:
        "logs/download_chembl_file/all.log",
    benchmark:
        "benchmark/download_chembl_file/all.tsv"
    params:
        URL=config["chembl_smiles_url"],
    shell:
        "curl -L --output {output} {params.URL} "
        "> {log} 2>&1"

# 2) Unzip the downloaded gz file
rule unzip_chembl_file:
    input:
        config["chembl_smiles_gz_file"],
    output:
        config["chembl_smiles_csv_file"],
    log:
        "logs/unzip_chembl_file/all.log",
    benchmark:
        "benchmark/unzip_chembl_file/all.tsv"
    shell:
        "gunzip -c {input} > {output} "


# 3 and 4) analyze the chembl molecules, save to TSV
rule apply_lilly_demerits:
    input:
        config["chembl_smiles_csv_file"]
    output:
        config["lilly_demerits_tsv_file"]
    log:
        "logs/apply_lilly_demerits/all.log",
    benchmark:
        "benchmark/apply_lilly_demerits/all.tsv"
    params:
        smiles_col=config["chembl_csv_file_smiles_col"],
        name_col=config["chembl_csv_file_name_col"],
        n_jobs=config["lilly_demerits_n_jobs"]
    shell:
        "python ../src/apply_lilly_demerits.py "
        "--input_dsv_file {input} "
        "--output_tsv {output} "
        "--smiles_column {params.smiles_col} "
        "--name_column {params.name_col} "
        "--iheader "
        "--idelim , "
        "--n_jobs {params.n_jobs} "
        "> {log} 2>&1"
