## About
This subdirectory contains [Snakemake](https://snakemake.readthedocs.io/en/stable/index.html) modules for running a workflow which creates the Badapple2 DB.

## badapple2
The steps below describe how to recreate the Badapple2 DB "from-scratch".
1. Download preliminary files:
    * [DrugCentral TSV file](https://unmtid-dbs.net/download/DrugCentral/2021_09_01/structures.smiles.tsv)
    * [PubChem DataSources file](https://pubchem.ncbi.nlm.nih.gov/rest/pug/sourcetable/all/CSV/?response_type=save&response_basename=PubChemDataSources_all)
2. (Optional) Move the downloaded files above to a different directory.
3. Modify the file paths in `config.yaml` to match your system
    * You really only need to modify `BASE_DATA_DIR`, `ASSAY_DATA_DIR`, `PUBCHEM_DATASOURCES_CSV`, `DRUG_CENTRAL_FILE`, and `LOCAL_PUBCHEM_DIRECTORY`.


## Commands
* `snakemake -s Snakefile_targets -np`