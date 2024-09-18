# Author: Jack Ringer
# Date: 7/29/2024
# Description:
# Initialize and load data into badapple_classic DB
# Note that this script is similar to load_db.sh but makes some formatting changes to account for the badapple 1 data
# based on: https://github.com/unmtransinfo/Badapple/blob/ae50bb04a58752933a807170b3d79c8906221500/sh/Go_badapple_DbLoad.sh

# run create_db_compare.sh BEFORE running this script

# tip: run export PGPASSWORD=<your_pw> before running this script to avoid psql prompts for pw
DB_NAME="badapple_classic"
DB_HOST="localhost"
SCHEMA="public"
ASSAY_ID_TAG="aid"
DB_USER="<your_user>"
DB_PASSWORD="<your_password>"


# path to directory of this repo (Badapple2)
REPO_DIR="/home/jack/unm_gra/Badapple2"
# make working dir to call scripts
cd $REPO_DIR

# path to directory where all input CSV files stored
DATA_DIR="/media/jack/big_disk/data/badapple/badapple1_inputs"

# 1) initialize DB
bash badapple1_comparison/sh_scripts/db/create_db.sh $DB_NAME $DB_HOST $SCHEMA "Badapple Comparison DB (dev version, PubChem-based)" 

# 2) load in CSV/TSV files (compounds, scaffolds, activity data)
bash badapple1_comparison/sh_scripts/db/load_csv_files.sh $DB_NAME $DB_HOST $SCHEMA $REPO_DIR $DATA_DIR

# 3) create mol tables for structural searching
bash badapple1_comparison/sh_scripts/db/create_mol_tables.sh $DB_NAME $DB_HOST $SCHEMA $REPO_DIR

# 4) index tables for better performance
bash badapple1_comparison/sh_scripts/db/index_tables.sh $DB_NAME $DB_HOST $SCHEMA

# 5) annotate compound and scaffold table with activity stats
bash badapple1_comparison/sh_scripts/db/annotate_assaystats.sh $DB_NAME $DB_HOST $SCHEMA $ASSAY_ID_TAG $DB_USER $DB_PASSWORD $REPO_DIR

# 6) annotate 'in_drug'
bash badapple1_comparison/sh_scripts/db/annotate_in_drug.sh $DB_NAME $DB_HOST $SCHEMA $ASSAY_ID_TAG $DB_USER $DB_PASSWORD $REPO_DIR $DATA_DIR

# 7) annotate scaffold scores+ranking
bash badapple1_comparison/sh_scripts/db/annotate_scores.sh $DB_NAME $DB_HOST $SCHEMA $ASSAY_ID_TAG $DB_USER $DB_PASSWORD $REPO_DIR $DATA_DIR