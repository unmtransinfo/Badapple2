"""
@author Jack Ringer
Date: 3/25/2026
Description:
Snakemake workflow which:
1) Downloads a csv.gz file containing the SMILES structures of all compounds in ChEMBL (version 35)
2) Unzips the csv.gz file to a CSV
"""


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
        "curl -L --output {output} {params.URL} " "> {log} 2>&1"


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
