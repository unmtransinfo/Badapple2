## About

This subdirectory contains [Snakemake](https://snakemake.readthedocs.io/en/stable/index.html) modules for running a workflow which creates the Badapple2 DB. It also contains the [Snakefile_NATA](Snakefile_NATA) workflow for testing different NAT thresholds when computing pScores and related statistics.

If you have not already done so, please setup both conda and PostgreSQL on your system by following the instructions [here](../README.md#code-usage).

## badapple2

The steps below describe how to recreate the Badapple2 DB "from-scratch".

1. Modify the params in [config.yaml](config.yaml) to match your system
   - You really only need to modify the following:
     - `BASE_DATA_DIR`
     - `ASSAY_DATA_DIR`
     - `DRUG_CENTRAL_DIR`
     - `LOCAL_PUBCHEM_DIR`
     - `DB_USER`
     - `DB_PASSWORD`
   - **NOTE:** Do not use spaces (' ') or other whitespace in any file names/paths. It will cause issues with paths being interpreted as multiple arguments.
2. Activate the badapple2 conda environment: `conda activate badapple2`
3. (Optional): Verify the snakemake workflow will run smoothly: `snakemake -np`
4. (Optional): Run `export PGPASSWORD=<your_password>` - avoids password prompts during the DB build process.
5. Run the first part of the workflow (downloading PubChem files/data): `snakemake --until get_assay_descriptions get_assay_annotations get_assay_targets --cores 1`
   - **NOTE ON REPRODUCIBILITY:** Please see [the note below](#note-on-reproducibility).
   - Have to run this first part of the workflow with 1 core because fetching information using the PubChem API is rate limited to 5 requests/second (see [here](https://pubchem.ncbi.nlm.nih.gov/docs/programmatic-access)). Will get error along the lines of "Network is unreachable" if trying to run multiple API calls in parallel.
   - Tip: If you want to monitor the progress of a specific rule `<rule_name>`, you can use the following command: `watch -n 1 "tail -c 70 logs/<rule_name>/all.log"`
6. Run rest of snakemake workflow to build the badapple2 DB: `snakemake`
   - If you want to limit the number of CPU cores used by the workflow, use
     `snakemake --cores <n>`
7. Verify that you can access the badapple2 DB: `psql -d badapple2`

### Additional Snakemake commands

For more information about Snakemake and additional arguments/commands see the [Snakemake documentation](https://snakemake.readthedocs.io/en/stable/)

- Creating a diagram of the workflow: `snakemake --forceall --rulegraph | dot -Tsvg > rulegraph.svg` (you can replace `svg` with the desired filetype)
- Create a diagram of workflow, labeling rules which have already been run: `snakemake --dag | dot -Tsvg > dag_sub.svg`
- Running the workflow until a certain rule completes: `snakemake --until <rule_name>`
- Re-run a particular rule and all rules which come after: `snakemake -R <rule_name>`
- Re-run the entire workflow: `snakemake --forceall`

### Workflow Diagram

Below is a the output of `snakemake --forceall --rulegraph | dot -Tsvg > rulegraph.svg`:

![rulegraph](https://github.com/user-attachments/assets/2746ddd0-fdda-4f12-80c6-0f15a5793619)

### Note on reproducibility

PubChem is a living database, and assay records can be updated over time. Although we don't expect these changes to make a significant impact, if you would like to guarantee that your version of badapple2 is the exact same as the version used by the web app, then it is advised to download and use all of the original input files:

https://unmtid-dbs.net/download/Badapple2/badapple2_files/

Follow these steps to run the workflow using the original files:

1. Create an empty `LOCAL_PUBCHEM_DIR`: `mkdir -p <LOCAL_PUBCHEM_DIR>`
   - We won't actually be adding data to this directory - we just create it to tell Snakemake that it exists
2. Go to your `BASE_DATA_DIR`: `cd <BASE_DATA_DIR>`
3. Download all the original input files:

```
wget -r -np -nH --cut-dirs=3 -R "index.html*" https://unmtid-dbs.net/download/Badapple2/badapple2_files/
```

4. Set `ASSAY_DATA_DIR` to `<BASE_DATA_DIR>/assays/` and `DRUG_CENTRAL_DIR` to `<BASE_DATA_DIR>/drugcentral/`
5. Touch the appropriate rules (tells Snakemake they don't need to be run):

```
snakemake --touch --until get_assay_descriptions get_assay_annotations get_assay_targets get_pubchem_assay_activities download_drugcentral_struct_file
```

6. Verify that the appropriate rules will be run: `snakemake -np`
   - There should be 20 rules total to be run
   - You can use `snakemake --dag | dot -Tsvg > dag_sub.svg` and verify that it looks like the diagram below
7. Run the rest of the workflow: `snakemake`

#### Workflow diagram after downloading files

![dag_sub](https://github.com/user-attachments/assets/a2d465ab-ba3c-4224-bbb2-c7f76d651f19)

## badapple2 Number of Assays Tested Analysis (NATA)

The [Snakefile_NATA](Snakefile_NATA) workflow is used to test different NAT thresholds. Here, NAT refers to the number of unique assays a compound was tested in (`nass_tested` in the `compound` table). The set NAT threshold determines which compounds are used when labeling scaffold pScores and related statistics (for example, if NAT=50 then only information from compounds tested in 50 or more assays will be considered when labeling pScores).

The workflow will create copies of the `scaffold` table, modify the statistics and pScores according to the given NAT threshold(s), and output figures visualizing the distribution of the resulting pScores and how they compare to pScores from badapple_classic. Note that the outputs of this workflow for the default values (NAT=1,25,50,75,100) can be downloaded from: https://unmtid-dbs.net/download/Badapple2/badapple2_NATA/NATA/ .

To run the workflow yourself follow these steps:

1. Modify [config_NATA.yaml](config_NATA.yaml) to match your requirements
2. Activate the badapple2 conda environment: `conda activate badapple2`
3. (Optional): Verify the snakemake workflow will run smoothly: `snakemake --snakefile Snakefile_NATA -np`
4. Run the workflow: `snakemake --snakefile Snakefile_NATA`

### Workflow Diagram

Below is the output of `snakemake --snakefile Snakefile_NATA --forceall --rulegraph | dot -Tsvg > rulegraph_NATA.svg`:
