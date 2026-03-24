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
        config["chembl_smiles_file"],

# 1) Download gz file
rule download_chembl_file:
    output:
        config["chembl_smiles_file"],
    log:
        "logs/download_gz_file/all.log",
    benchmark:
        "benchmark/download_gz_file/all.tsv"
    params:
        URL=config["chembl_smiles_url"],
    shell:
        "wget {params.URL} -O {output} " 
        "> {log} 2>&1"
