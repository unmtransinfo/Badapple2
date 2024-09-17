# About
The steps outlined in this README provide information on how to generate a comparison DB (badapple_comparison) to the Badapple1 DB (badapple) using the updated code. In particular, badapple_comparison differs from badapple in the following ways:
* badapple_comparison uses HierS scaffold definitions from [ScaffoldGraph](https://github.com/UCLCheminformatics/ScaffoldGraph) rather than the Java-based implementation of HierS from [UNM_BIOCOMP_HSCAF](https://github.com/unmtransinfo/unm_biocomp_hscaf).
* badapple_comparison uses newer version of PostgreSQL with minor differences in median calculation (using `SELECT PERCENTILE_CONT(0.5)` instead of [create_median_function.sql](https://github.com/unmtransinfo/Badapple/blob/master/sql/create_median_function.sql)).

The steps for generating badapple_comparison are slightly different than badapple2 because badapple and badapple_comparison use compounds from [MLSMR](https://pubchem.ncbi.nlm.nih.gov/source/MLSMR), rather than the set of PubChem compounds found from a given list of AIDs (like badapple2). Thus, the steps below are followed to help provide a more direct comparison between badapple and badapple_comparison (since both DBs will have the exact same set of compounds).


## Database (DB) Easy Setup
The steps below provide info on how to setup the badapple_comparison and original badapple DB. 

1. Setup PostgreSQL on your system: see [here](https://www.postgresql.org/download/)
2. Download [badapple_comparison.pgdump](https://unmtid-dbs.net/download/Badapple2/badapple_comparison.pgdump)
3. Load DB from dump file: `pg_restore -O -x -v -C -d badapple_comparison badapple_comparison.pgdump` 
4. Configure user:
    ```
    psql -c "CREATE ROLE myname WITH LOGIN PASSWORD 'foobar'"
    psql -c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO myname"
    psql -c "GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO myname"
    psql -c "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO myname"
    ```
5. (Optional) If you'd like to download the original Badapple DB for running comparisons, follow the steps [here](https://github.com/unmtransinfo/Badapple?tab=readme-ov-file#database-installation)

## DB Advanced Setup (Development/from-scratch)
**You can skip this section if you setup the DB(s) using the steps from above**

The steps below outline how one can re-create the Badapple1 DB on their own system, using the updated code within this repo (note that the HierS implementation has changed).

Make sure to inspect all bash scripts and **modify variable definitions** (mostly file paths) as needed before running them. When running bash scripts, make sure your conda environment is active (`conda activate badapple2`).

### Requirements
You will need ~3.5 GB of space to store the Badapple1 CSV files used to initialize the DB. Additionally, the badapple_comparison DB will take
~12 GB of space, although this is reduced if one drops the "activity" table after constructing the rest of the DB.

### (1) Preliminary
First we'll gather the data used for Badapple1.

1. Change your directory to where you want to save the files.
2. Copy over the input CSV files used for Badapple1:
```
scp <your_username>@chiltepin.health.unm.edu:/home/data/Badapple/data/\{pc_mlsmr_compounds.smi,pc_mlsmr_mlp_assaystats_act.csv.gz,pc_mlsmr_sid2cid.csv,drugcentral.smi} .
```
3. Unzip the assaystats file:
```
gunzip pc_mlsmr_mlp_assaystats_act.csv.gz
```
4. (Optional) If you want to setup the original badapple database on your system so that you can run comparisons, see the steps in the Badapple repo [here](https://github.com/unmtransinfo/Badapple?tab=readme-ov-file#database-installation). This DB takes up ~800 MB. 

### (2) Generate Scaffolds
Run `bash badapple1_comparison/sh_scripts/run_generate_scaffolds.sh`. This will generate 3 output files:
* `o_mol`: TSV file with all compounds and their CIDs
* `o_scaf`: TSV file with all scaffolds and their IDs
* `o_mol2scaf`: TSV file mapping compound CID to scaffold ID(s)

### (3) Initializing the DB
1. Install postgresql with the RDKit cartridge (requires sudo):
`apt install postgresql-14-rdkit`
2. Run `bash badapple1_comparison/sh_scripts/create_and_load_db.sh`
3. (Optional) Drop the activity table to save storage: 
    
    `psql -d badapple_comparison -c "DELETE FROM activity"`

## (Optional) Compare the badapple DB and badapple_comparison DB
* You can compare the sets of compounds and scaffolds between the original badapple DB and badapple_comparison using `psql -d badapple -f src/sql/compare_compounds.sql` and `psql -d badapple -f src/sql/compare_scaffolds.sql`. You can also compare the compound<->scaffold relationships using `psql -d badapple -f src/sql/compare_compound_scaf_relationships.sql`.
* You can use `psql -d badapple -f src/sql/compare_compounds_stats.sql` and `psql -d badapple -f src/sql/compare_scaffold_stats.sql` to compare the two DB activity annotations.
* You can run `python src/check_scaf_diffs.py` to check that any differences in scaffold annotations are due only to differences in compound<->scaffold relationships.
* [assay_comparison.ipynb](src/notebooks/assay_comparison.ipynb) reviews assay statistics between badapple and badapple_comparison
* [score_comparison.ipynb](src/notebooks/score_comparison.ipynb) reviews the differences in scaffold scores between badapple and badapple_comparison