## About
This subdirectory contains [Snakemake](https://snakemake.readthedocs.io/en/stable/index.html) modules for running a workflow which creates the Badapple2 DB.

## badapple2
The steps below describe how to recreate the Badapple2 DB "from-scratch".
1. Modify the file paths in `config.yaml` to match your system
    * You really only need to modify `BASE_DATA_DIR`, `ASSAY_DATA_DIR`, `DRUG_CENTRAL_DIR`, and `LOCAL_PUBCHEM_DIR`.
    * **NOTE:** Do not use spaces (' ') or other whitespace in any file names/paths. It will cause issues with paths being interpreted as multiple arguments.


## Commands
* `snakemake -s Snakefile_targets -np`