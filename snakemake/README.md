## About
This subdirectory contains [Snakemake](https://snakemake.readthedocs.io/en/stable/index.html) modules for running a workflow which creates the Badapple2 DB.

## badapple2
The steps below describe how to recreate the Badapple2 DB "from-scratch".
1. Modify the file paths in `config.yaml` to match your system
    * You really only need to modify `BASE_DATA_DIR`, `ASSAY_DATA_DIR`, `DRUG_CENTRAL_DIR`, and `LOCAL_PUBCHEM_DIR`.
    * **NOTE:** Do not use spaces (' ') or other whitespace in any file names/paths. It will cause issues with paths being interpreted as multiple arguments.
2. Modify the DB params in `config.yaml`, in particular `DB_USER` and `DB_PASSWORD`
3. (Optional): Run run `export PGPASSWORD=<your_password>` - avoids password prompts during the DB build process.
4. Run snakemake workflow to build the badapple2 DB: `snakemake`
    * If you want to limit the number of CPU cores used by the workflow, use
    `snakemake --cores <n>`
5. Verify that you can access the badapple2 DB: `psql -d badapple2`


### Additional Snakemake commands
For more information about Snakemake and additional arguments/commands see the [Snakemake documentation](https://snakemake.readthedocs.io/en/stable/)
* Creating a diagram of the workflow: `snakemake --forceall --rulegraph | dot -Tsvg > rulegraph.svg` (you can replace `svg` with the desired filetype)
* Running the workflow until a certain rule completes: `snakemake --until <rule_name>` 
* Re-run a particular rule and all rules which come after: `snakemake -R <rule_name>`
* Re-run the entire workflow: `snakemake --forceall`