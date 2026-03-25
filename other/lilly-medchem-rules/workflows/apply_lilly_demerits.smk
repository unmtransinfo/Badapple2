"""
@author Jack Ringer
Date: 3/24/2026
Description:
Snakemake workflow which:
1) Analyzes a dataset using Medchem's implementation of Lilly demerits (https://github.com/datamol-io/medchem/tree/main/medchem/structural/lilly_demerits)
2) Saves the results to a TSV file
"""


rule apply_lilly_demerits:
    input:
        config["lilly_demerits_input_file"],
    output:
        config["lilly_demerits_output_file"],
    log:
        "logs/apply_lilly_demerits/all.log",
    benchmark:
        "benchmark/apply_lilly_demerits/all.tsv"
    params:
        smiles_col=config["lilly_demerits_input_smiles_col"],
        name_col=config["lilly_demerits_input_name_col"],
        idelim=config["lilly_demerits_input_delim"],
        n_jobs=config["lilly_demerits_n_jobs"],
    shell:
        "python src/apply_lilly_demerits.py "
        "--input_dsv_file {input} "
        "--output_tsv {output} "
        "--smiles_column {params.smiles_col} "
        "--name_column {params.name_col} "
        "--iheader "
        "--idelim {params.idelim} "
        "--n_jobs {params.n_jobs} "
        "> {log} 2>&1"
