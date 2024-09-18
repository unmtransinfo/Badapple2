# About
The steps outlined in this README provide information on how to download/recreate the classic version of Badapple (badapple_classic) using the updated code. There are also steps for comparing badapple_classic to the [original Badapple DB](https://github.com/unmtransinfo/Badapple/) (badapple). 

badapple_classic differs from badapple in the following ways:
* badapple_classic uses HierS scaffold definitions from [ScaffoldGraph](https://github.com/UCLCheminformatics/ScaffoldGraph) rather than the Java-based implementation of HierS from [UNM_BIOCOMP_HSCAF](https://github.com/unmtransinfo/unm_biocomp_hscaf).
* badapple_classic uses a newer version of PostgreSQL with minor differences in median calculation (using `SELECT PERCENTILE_CONT(0.5)` instead of [create_median_function.sql](https://github.com/unmtransinfo/Badapple/blob/master/sql/create_median_function.sql)).

The steps for generating badapple_classic are different than badapple2 because badapple and badapple_classic use identical input files (each containing data with a date cutoff of 2017-08-14):
* [pc_mlsmr_compounds.smi](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/pc_mlsmr_compounds.smi) - list of compounds with Isomeric SMILES and PubChem compound IDs (CIDs).
* [pc_mlsmr_mlp_assaystats_act.csv](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/pc_mlsmr_mlp_assaystats_act.csv) - assay results by assay ID (AID), substance ID (SID), and activity outcome.
* [pc_mlsmr_sid2cid.csv](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/pc_mlsmr_sid2cid.csv) - list of PubChem SIDs mapped to CIDs.
* [drugcentral.smi](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/drugcentral.smi) - list of drugs from [DrugCentral](https://drugcentral.org/).

## Database (DB) Easy Setup
The steps below provide info on how to setup the badapple_classic and original badapple DB. 

1. Install postgresql with the RDKit cartridge (requires sudo):
`apt install postgresql-14-rdkit`
2. Download [badapple_classic.pgdump](https://unmtid-dbs.net/download/Badapple2/badapple_classic.pgdump).
3. Load DB from dump file: `pg_restore -O -x -v -C -d badapple_classic badapple_classic.pgdump` 
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
You will need ~3.5 GB of space to store the CSV files used to initialize the DB. Additionally, the badapple_classic DB will take
~12 GB of space, although this is reduced if one drops the "activity" table after constructing the rest of the DB.

### (1) Preliminary
First we'll gather the data used for badapple_classic.

1. Change your directory to where you want to save the files.
2. Download the input files for badapple_classic from [this directory](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/).
3. (Optional) If you want to setup the original badapple database on your system so that you can run comparisons, see the steps in the Badapple repo [here](https://github.com/unmtransinfo/Badapple?tab=readme-ov-file#database-installation). This DB takes up ~800 MB. 

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
    
    `psql -d badapple_classic -c "DELETE FROM activity"`

## (Optional) Compare the badapple DB and badapple_classic DB
* You can compare the sets of compounds and scaffolds between the original badapple DB and badapple_classic using `psql -d badapple -f src/sql/compare_compounds.sql` and `psql -d badapple -f src/sql/compare_scaffolds.sql`. You can also compare the compound<->scaffold relationships using `psql -d badapple -f src/sql/compare_compound_scaf_relationships.sql`.
* You can use `psql -d badapple -f src/sql/compare_compounds_stats.sql` and `psql -d badapple -f src/sql/compare_scaffold_stats.sql` to compare the two DB activity annotations.
* You can run `python src/check_scaf_diffs.py` to check that any differences in scaffold annotations are due only to differences in compound<->scaffold relationships.
* [assay_comparison.ipynb](src/notebooks/assay_comparison.ipynb) reviews assay statistics between badapple and badapple_classic
* [score_comparison.ipynb](src/notebooks/score_comparison.ipynb) reviews the differences in scaffold scores between badapple and badapple_classic