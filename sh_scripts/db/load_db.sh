# author Jack Ringer
# Date: 7/29/2024
# Description:
# Load data into badapple2 DB
# based on: https://github.com/unmtransinfo/Badapple/blob/ae50bb04a58752933a807170b3d79c8906221500/sh/Go_badapple_DbLoad.sh#L73

# tip: run export PGPASSWORD=<your_pw> before running this script to avoid psql prompts for pw
DB_NAME="badapple2"
DB_HOST="localhost"
SCHEMA="public"
ASSAY_ID_TAG="aid"

#path to directory of this repo (Badapple2)
REPO_DIR="/home/jack/unm_gra/Badapple2"
# make working dir to call scripts
cd $REPO_DIR

# path to directory where all input TSV files stored
DATA_DIR="/media/jack/big_disk/data/badapple2"

# NOTE: using temp tables in psql commands to rename/drop columns from input TSVs

# Step 1) Load scafs with scafids + scaf2scaf relationship
# expects SCAF_TSV_FILE to have header: scaffold_id, smiles, hierarchy, scaf2scaf (TSV-separated)
# (output from generate_scaffolds.py)
SCAF_TSV_FILE="scafs.tsv"
SCAF_TSV_PATH="$DATA_DIR/$SCAF_TSV_FILE"
echo "Adding scafs table..."
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_scaf (
    scaffold_id INTEGER PRIMARY KEY,
    smiles VARCHAR(512) NOT NULL,
    hierarchy INTEGER,
    scaf2scaf VARCHAR(2048)
);
\COPY temp_scaf (scaffold_id, smiles, hierarchy, scaf2scaf) FROM '$SCAF_TSV_PATH' DELIMITER E'\t' CSV HEADER;
INSERT INTO scaffold (id, scafsmi, scaftree) SELECT scaffold_id, smiles, scaf2scaf FROM temp_scaf;
DROP TABLE temp_scaf;
EOF

# Step 2) Load scaf2cpd links
SCAF2CPD_TSV_FILE="scaf2cpd.tsv"
SCAF2CPD_TSV_PATH="$DATA_DIR/$SCAF2CPD_TSV_FILE"
echo "Adding scaf2cpd table..."
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_scaf2cpd (
    mol_id INTEGER PRIMARY KEY,
    mol_name VARCHAR(512) NOT NULL,
    hierarchy INTEGER,
    scaf2scaf VARCHAR(2048)
);
\COPY temp_scaf2cpd (scaffold_id, smiles, hierarchy, scaf2scaf) FROM '$SCAF_TSV_PATH' DELIMITER E'\t' CSV HEADER;
INSERT INTO scaf2cpd (scafid, cid) SELECT  FROM temp_scaf2cpd;
DROP TABLE temp_scaf2cpd;
EOF