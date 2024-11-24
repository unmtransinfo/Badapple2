# Author: Jack Ringer
# Date: 11/22/2024
# Description:
# Load TSV files from DrugCentral data into DB (creates "drug" table)

if [ $# -lt 5 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA DRUG_CENTRAL_TSV_PATH DRUG_TSV_PATH\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3
DRUG_CENTRAL_TSV_PATH=$4
DRUG_TSV_PATH=$5

# NOTE: using temp tables in psql commands to rename/drop columns from input TSVs

# Step 1) Load drug table
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_drug (
    temp_id INTEGER,
	cansmi VARCHAR(2048),
    drug_id INTEGER NOT NULL,
	inn VARCHAR(128) 
);
CREATE TEMP TABLE temp_drug2 (
    SMILES VARCHAR(2048),
    InChI TEXT,
    InChIKey VARCHAR(2048),
    ID INTEGER NOT NULL,
    INN VARCHAR(128),
    CAS_RN VARCHAR(128)
);
\COPY temp_drug (temp_id, cansmi, drug_id) FROM '$DRUG_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
\COPY temp_drug2 (SMILES, InChI, InChIKey, ID, INN, CAS_RN) FROM '$DRUG_CENTRAL_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
-- add drug name (INN) using original drugcentral file
UPDATE temp_drug td
SET inn = td2.INN
FROM temp_drug2 td2
WHERE td.drug_id = td2.ID;
--now can insert completed data into drug table
INSERT INTO ${SCHEMA}.drug (drug_id, cansmi, inn) SELECT drug_id, cansmi, inn FROM temp_drug;
DROP TABLE temp_drug;
DROP TABLE temp_drug2;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.drug IS 'Drug information from DrugCentral. The drug_id column matches ids from DrugCentral. The inn column is the International Nonproprietary Name (INN)'"
echo "Loaded drug table."