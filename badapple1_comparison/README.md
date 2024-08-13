# About
The steps outlined in this README provide information on how to generate a comparison DB to the Badapple1 DB using the updated code. These steps are different because Badapple1 uses compounds from [MLSMR](https://pubchem.ncbi.nlm.nih.gov/source/MLSMR), rather than the set of PubChem compounds found from a given list of AIDs (like Badapple2).

## Requirements
You will need ~3.5 GB of space to store the Badapple1 CSV files used to initialize the DB.

## Database (DB) Development Setup
The steps below outline how one can re-create the Badapple1 DB on their own system, using the updated code within this repo (note that the HierS implementation has changed).

Make sure to inspect all bash scripts and **modify variable definitions** (mostly file paths) as needed before running them. When running bash scripts, make sure your conda environment is active (`conda activate badapple2`).

### (1) Preliminary
First we'll gather the data used for Badapple1.

1. Change your directory to where you want to save the files.
2. Copy over the input CSV files used for Badapple1:
```
scp <your_username>@chiltepin:/home/data/Badapple/data/\{pc_mlsmr_compounds.smi,pc_mlsmr_mlp_assaystats_act.csv.gz,pc_mlsmr_sid2cid.csv} .
```
3. Unzip the assaystats file:
```
gunzip pc_mlsmr_mlp_assaystats_act.csv.gz
```

### (2) Generate Scaffolds
Run `bash badapple1_comparison/sh_scripts/run_generate_scaffolds.sh`. This will generate 3 output files:
* `o_mol`: TSV file with all compounds and their CIDs
* `o_scaf`: TSV file with all scaffolds and their IDs
* `o_mol2scaf`: TSV file mapping compound CID to scaffold ID(s)

### (3) Initializing the DB
1. Install postgresql with the RDKit cartridge (requires sudo):
`apt install postgresql-14-rdkit`
2. Run `bash badapple1_comparison/sh_scripts/create_db_compare.sh`
3. Run `bash badapple1_comparison/sh_scripts/load_db_compare.sh`
4. Run `bash badapple1_comparison/sh_scripts/annotate_db.sh`
    * At the time of writing, this process takes several hours. I will work on making it faster.