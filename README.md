# Badapple2
Bioassay data associative promiscuity pattern learning engine V2. 

## System Requirements
Code is expected to work on Linux systems. Thus far all code has been tested on the following OS:
```
Distributor ID:	Linuxmint
Description:	Linux Mint 21.2
Release:	21.2
Codename:	victoria
```

## Python Setup
1. Setup conda (see the [Miniconda Site](https://conda.github.io/conda-libmamba-solver/user-guide/) for more info) 
    * (Optional) I'd recommend using the libmamba solver for faster install times, see [here](https://conda.github.io/conda-libmamba-solver/user-guide/)
2. Install the Badapple2 environment: `conda env create -f environment.yml`
    * This will create a new conda env with name `badapple2`. If you wish, you can change the first line of [environment.yml](environment.yml) prior to the command above to change the name.

## Database (DB) Development Setup
**NOTE:** If creating a Badapple1 comparison DB, follow the instructions [here](badapple1_comparison/README.md).

The steps below outline how one can generate the Badapple2 DB on their own system.

Make sure to inspect all bash scripts and **modify variable definitions** (mostly file paths) as needed before running them. When running bash scripts, make sure your conda environment is active (`conda activate badapple2`).

### (1) Preliminary
Before getting started, make sure you have the following files:

* AID file: Text file listing all PubChem AIDs to be included in the DB.

### (2) Input Data
The steps below outline how to mirror PubChem data to your system (much faster/more reliable than using PUG-REST API) and how to generate the 5 input TSVs we'll use in part (3). I would recommend saving all 5 of these TSVs to the same directory.

1. Run `bash sh_scripts/mirror_pubchem.sh`
    * This will mirror PubChem Bioassay data on your system (~11 GB of space required).
    * Files will be saved to `{workdir}/bioassay`.
2. Run `bash sh_scripts/python/run_pubchem_assays_local.sh`. This will generate 3 files:
    * `o_compound`: TSV file with compound CIDs and isomeric SMILES.
    * `o_sid2cid`: TSV file mapping compound id (CID) <=> substance id (SID)
    * `o_assaystats`: TSV file with assay id (AID), substance id (SID), and activity outcome.
3. Run `bash sh_scripts/python/run_generate_scaffolds.sh`. This will generate 3 output files:
    * `o_mol`: TSV file with compound canonical SMILES and their CIDs
    * `o_scaf`: TSV file with all scaffolds and their IDs
    * `o_mol2scaf`: TSV file mapping compound CID to scaffold ID(s)

### (3) Initializing the DB
(Step 6 currently out of date, will update after Badapple1 comparison complete)

1. Install postgresql with the RDKit cartridge (requires sudo):
`apt install postgresql-14-rdkit`
2. Run `bash sh_scripts/db/create_db.sh`
3. Connect to db with `psql -d badapple2`
4. Run `CREATE EXTENSION rdkit;`. This should return `CREATE EXTENSION`.
5. (Optional) You can test that the RDKit cartridge is working with the `is_valid_smiles` command:
```
badapple2=# select is_valid_smiles('O1OCCCC1');
 is_valid_smiles 
-----------------
 t
(1 row)
```
6. Run `bash sh_scripts/db/load_db.sh`
7. Done!