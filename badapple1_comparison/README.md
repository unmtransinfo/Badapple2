# About
The steps outlined in this README provide information on how to download/recreate the classic version of Badapple (badapple_classic) using the updated code. There are also steps for comparing badapple_classic to the [original Badapple DB](https://github.com/unmtransinfo/Badapple/) (badapple). 

badapple_classic differs from badapple in the following ways:
* badapple_classic uses HierS scaffold definitions from [ScaffoldGraph](https://github.com/UCLCheminformatics/ScaffoldGraph) rather than the Java-based implementation of HierS from [UNM_BIOCOMP_HSCAF](https://github.com/unmtransinfo/unm_biocomp_hscaf).
* badapple_classic uses a newer version of PostgreSQL with minor differences in median calculation (using `SELECT PERCENTILE_CONT(0.5)` instead of [create_median_function.sql](https://github.com/unmtransinfo/Badapple/blob/master/sql/create_median_function.sql)).
* badapple_classic generates canonical SMILES using [RDKit](https://www.rdkit.org/), whereas badapple used [openbabel](http://openbabel.org/index.html).

The steps for generating badapple_classic are different than badapple2 because badapple and badapple_classic use identical input files (each containing data with a date cutoff of 2017-08-14):
* [pc_mlsmr_compounds.smi](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/pc_mlsmr_compounds.smi) - list of compounds with Isomeric SMILES and PubChem compound IDs (CIDs).
* [pc_mlsmr_mlp_assaystats_act.csv](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/pc_mlsmr_mlp_assaystats_act.csv) - assay results by assay ID (AID), substance ID (SID), and activity outcome.
* [pc_mlsmr_sid2cid.csv](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/pc_mlsmr_sid2cid.csv) - list of PubChem SIDs mapped to CIDs.
* [drugcentral.smi](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/drugcentral.smi) - list of drugs from [DrugCentral](https://drugcentral.org/).

Additionally, one can view the set of PubChem assay IDs used for badapple and badapple_classic from the following file (this file is generated when creating the DB):
* [badapple_classic_tested.aid](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/badapple_classic_tested.aid)

## Database (DB) Easy Setup
The steps below provide info on how to set up the badapple_classic DB. 


### Option 1: Docker
Use this option to install a Docker image with the DB.


See the docker README file [here](../docker/README.md#badapple_classic)


### Option 2: PostgreSQL
Use this option to install the DB directly on your system using PostgreSQL.

1. Follow the PostgreSQL setup instructions [here](../README.md#postgresql-setup)
2. Download [badapple_classic.pgdump](https://unmtid-dbs.net/download/Badapple2/badapple_classic.pgdump).
3. Create the DB: `createdb badapple_classic`
3. Load DB from dump file: `pg_restore -O -x -v -d badapple_classic badapple_classic.pgdump`
4. If you followed (Option 2) in the setup, then you can grant permissions for user `<username>` to badapple_classic like so:
    ```
    sudo -i -u postgres
    psql -d badapple_classic -c "CREATE ROLE <username> WITH LOGIN PASSWORD '<password>'"
    psql -d badapple_classic -c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO <username>"
    psql -d badapple_classic -c "GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO <username>"
    psql -d badapple_classic -c "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO <username>"
    ```

## DB Advanced Setup (Development/from-scratch)
**You can skip this section if you setup the DB using the steps from above**

The steps below outline how one can create badapple_classic on their own system "from-scratch" (i.e., only using the input files mentioned above).

Make sure to inspect all bash scripts and **modify variable definitions** (mostly file paths) as needed before running them. When running bash scripts, make sure your conda environment is active (`conda activate badapple2`).

### Requirements
You will need ~3.5 GB of space to store the CSV files used to initialize the DB. Additionally, the badapple_classic DB will take
~12 GB of space, although this is reduced if one drops the "activity" table after constructing the rest of the DB.

### (1) Setup
See [here](../README.md#1-setup).

### (2) Preliminary
First we'll gather the data used for badapple_classic.

1. Change your directory to where you want to save the files.
2. Download the input files for badapple_classic from [this directory](https://unmtid-dbs.net/download/Badapple2/badapple_classic_files/).

### (3) Generate Scaffolds
Run `bash badapple1_comparison/sh_scripts/run_generate_scaffolds.sh`. This will generate 3 output files:
* `o_mol`: TSV file with all compounds and their CIDs
* `o_scaf`: TSV file with all scaffolds and their IDs
* `o_mol2scaf`: TSV file mapping compound CID to scaffold ID(s)

### (4) Initializing the DB
1. Run `bash badapple1_comparison/sh_scripts/create_and_load_db.sh`
2. (Optional) Drop the activity table to save storage: 
    
    `psql -d badapple_classic -c "DELETE FROM activity"`

## (Optional) Compare the badapple DB and badapple_classic DB
The steps below provide instructions for downloading the original badapple DB and comparing it to badapple_classic.

1. Download the original Badapple DB by following the steps [here](https://github.com/unmtransinfo/Badapple?tab=readme-ov-file#database-installation).
2. Canonicalize the badapple scaffold SMILES using RDKit:
```
psql -d badapple -c "CREATE EXTENSION IF NOT EXISTS rdkit;UPDATE scaffold SET scafsmi = mol_to_smiles(mols_scaf.scafmol) FROM mols_scaf WHERE mols_scaf.id = scaffold.id;"
```
3. You can now run the comparison scripts:
    * You can compare the sets of compounds and scaffolds between the original badapple DB and badapple_classic using `psql -d badapple -f src/sql/compare_compounds.sql` and `psql -d badapple -f src/sql/compare_scaffolds.sql`. You can also compare the compound<->scaffold relationships using `psql -d badapple -f src/sql/compare_compound_scaf_relationships.sql`.
    * You can use `psql -d badapple -f src/sql/compare_compounds_stats.sql` and `psql -d badapple -f src/sql/compare_scaffold_stats.sql` to compare the two DB activity annotations.
    * You can run `python src/check_scaf_diffs.py` to check that any differences in scaffold annotations are due only to differences in compound<->scaffold relationships.
    * [assay_comparison.ipynb](src/notebooks/assay_comparison.ipynb) reviews assay statistics between badapple and badapple_classic
    * [score_comparison.ipynb](src/notebooks/score_comparison.ipynb) reviews the differences in scaffold scores between badapple and badapple_classic