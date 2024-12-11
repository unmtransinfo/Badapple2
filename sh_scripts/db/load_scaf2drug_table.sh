# Author: Jack Ringer
# Date: 11/22/2024
# Description:
# Create the "scaf2drug" table in Badapple 2.0 DB

if [ $# -lt 5 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA DRUG_SCAFFOLD_TSV_PATH DRUG_SCAF2CPD_TSV_PATH\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3
DRUG_SCAFFOLD_TSV_PATH=$4
DRUG_SCAF2CPD_TSV_PATH=$5

# for DB comments
HIERS_SCRIPT="generate_scaffolds.py"

# NOTE: using temp tables in psql commands to rename/drop columns from input TSVs
# Step 1) Load scaf2drug links
# expects input tsv to have header: mol_id	mol_name	scaffold_id
# assumes mol_name is drug_id (mol_id is just from counting)
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_scaf2drug (
    mol_id INTEGER NOT NULL,
    drug_id INTEGER NOT NULL,
    scafid INTEGER NOT NULL,
    canon_smiles VARCHAR(512)
);
CREATE TEMP TABLE temp_drug_scaf (
    scafid INTEGER,
    canon_smiles VARCHAR(512) NOT NULL,
    kekule_smiles VARCHAR(512) NOT NULL,
    hierarchy INTEGER,
    scaf2scaf VARCHAR(2048)
);
\COPY temp_scaf2drug (mol_id, drug_id, scafid) FROM '$DRUG_SCAF2CPD_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
\COPY temp_drug_scaf (scafid, canon_smiles, kekule_smiles, hierarchy, scaf2scaf) FROM '$DRUG_SCAFFOLD_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
-- insert smiles into temp_scaf2drug
UPDATE temp_scaf2drug ts
SET canon_smiles = ts2.canon_smiles
FROM temp_drug_scaf ts2
WHERE ts.scafid = ts2.scafid;
-- now get scafids from actual scaffold table
UPDATE temp_scaf2drug ts
SET scafid = s.id
FROM scaffold s
WHERE ts.canon_smiles = s.scafsmi;
-- remove entries in temp_scaf2drug if ts.canon_smiles is not in s.scafsmi
DELETE FROM temp_scaf2drug
WHERE canon_smiles NOT IN (SELECT scafsmi FROM scaffold);
-- now create scaf2drug
INSERT INTO ${SCHEMA}.scaf2drug (scafid, drug_id) SELECT scafid, drug_id FROM temp_scaf2drug;
DROP TABLE temp_scaf2drug;
DROP TABLE temp_drug_scaf;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.scaf2drug IS 'From ${DRUG_SCAFFOLD_TSV_PATH} via ${HIERS_SCRIPT}.'"
echo "Loaded scaf2cpd table."