"""
@author Jack Ringer
Date: 3/25/2026
Description:
Snakemake workflow which:
1) Analyzes a dataset using Badapple
2) Saves the results to a TSV file
"""


rule apply_badapple:
    input:
        config["badapple_input_file"],
    output:
        config["badapple_output_file"],
    log:
        "logs/apply_badapple/all.log",
    benchmark:
        "benchmark/apply_badapple/all.tsv"
    params:
        database=config["badapple_database"],
        smiles_col=config["badapple_input_smiles_col"],
        name_col=config["badapple_input_name_col"],
        idelim=config["badapple_input_delim"],
        max_rings=config["badapple_max_rings"],
        batch_size=config["badapple_batch_size"],
        local_port=config["badapple_api_local_port"],
    shell:
        "python src/get_compound_scores.py "
        "--input_dsv_file {input} "
        "--output_tsv {output} "
        "--database {params.database} "
        "--smiles_column {params.smiles_col} "
        "--name_column {params.name_col} "
        "--iheader "
        "--idelim {params.idelim} "
        "--max_rings {params.max_rings} "
        "--batch_size {params.batch_size} "
        "--local_port {params.local_port} "
        "> {log} 2>&1"
