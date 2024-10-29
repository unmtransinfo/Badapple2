# Author: Jack Ringer
# Date: 8/27/2024
# Description:
# Load CSV/TSV files into DB.

if [ $# -lt 5 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA REPO_DIR DATA_DIR\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3
REPO_DIR=$4
DATA_DIR=$5


# NOTE: using temp tables in psql commands to rename/drop columns from input TSVs

# for DB comments
HIERS_SCRIPT="generate_scaffolds.py"

# Step 1) Load scafs with scafids + scaf2scaf relationship
# expects SCAF_TSV_FILE to have header: scaffold_id	canon_smiles	kekule_smiles	hierarchy	scaf2scaf (TSV-separated)
# (output from ${HIERS_SCRIPT})
SCAF_TSV_FILE="scafs.tsv"
SCAF_TSV_PATH="$DATA_DIR/$SCAF_TSV_FILE"
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_scaf (
    scaffold_id INTEGER PRIMARY KEY,
    canon_smiles VARCHAR(512) NOT NULL UNIQUE,
    kekule_smiles VARCHAR(512) NOT NULL UNIQUE,
    hierarchy INTEGER,
    scaf2scaf VARCHAR(2048)
);
\COPY temp_scaf (scaffold_id, canon_smiles, kekule_smiles, hierarchy, scaf2scaf) FROM '$SCAF_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
INSERT INTO ${SCHEMA}.scaffold (id, scafsmi, kekule_scafsmi, scaftree) SELECT scaffold_id, canon_smiles, kekule_smiles, scaf2scaf FROM temp_scaf;
DROP TABLE temp_scaf;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.scaffold IS 'Scaffold definitions from HierS, see ${HIERS_SCRIPT}. Input file is ${SCAF_TSV_PATH}'"
echo "Loaded scafs table."


# Step 2) Load scaf2scaf table, uses "scaftree" column from "scaffold" table
SCAF2SCAF_SCRIPT="src/sql/fill_scaf2scaf.sql"
psql -h $DB_HOST -d $DB_NAME -f $SCAF2SCAF_SCRIPT
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.scaf2scaf IS 'Scaffold parentage from scaftree column in scaffold table, see ${SCAF2SCAF_SCRIPT}.'"
echo "Loaded scaf2scaf table."


# Step 3a) Load scaf2cpd links
# expects input tsv to have header: mol_id	mol_name	scaffold_id
# will be using mol_name as CID (original "names" given to mols was CID, mol_id is just from counting)
# (output from ${HIERS_SCRIPT})
SCAF2CPD_TSV_FILE="scaf2cpd.tsv"
SCAF2CPD_TSV_PATH="$DATA_DIR/$SCAF2CPD_TSV_FILE"
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_scaf2cpd (
    mol_id INTEGER NOT NULL,
    mol_name INTEGER NOT NULL,
    scaffold_id INTEGER
);
\COPY temp_scaf2cpd (mol_id, mol_name, scaffold_id) FROM '$SCAF2CPD_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
INSERT INTO ${SCHEMA}.scaf2cpd (scafid, cid) SELECT scaffold_id, mol_name FROM temp_scaf2cpd;
DROP TABLE temp_scaf2cpd;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.scaf2cpd IS 'From ${SCAF2CPD_TSV_PATH} via ${HIERS_SCRIPT}.'"
echo "Loaded scaf2cpd table."


# Step 3b) Load compounds with CIDs
CPD_TSV_FILE="pc_mlsmr_compounds.smi"
CPD_CANON_SMI_FILE="cpds.tsv"
CPD_TSV_PATH="$DATA_DIR/$CPD_TSV_FILE"
CPD_HIERS_TSV_PATH="$DATA_DIR/$CPD_CANON_SMI_FILE"
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_compound (
    CID INTEGER PRIMARY KEY,
    SMILES VARCHAR(512),
    ISOMERIC_SMILES VARCHAR(512) NOT NULL
);
-- to load in canon smiles
CREATE TEMP TABLE temp_compound2 (
    mol_id INTEGER PRIMARY KEY,
    SMILES VARCHAR(512) NOT NULL,
    CID INTEGER NOT NULL
);
\COPY temp_compound (ISOMERIC_SMILES, CID) FROM '$CPD_TSV_PATH' WITH (FORMAT CSV, DELIMITER ' ', HEADER false);
\COPY temp_compound2 (mol_id, SMILES, CID) FROM '$CPD_HIERS_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
-- add canonical (non-isomeric) SMILES from rdkit into temp_compound table
UPDATE temp_compound tc
SET SMILES = tc2.SMILES
FROM temp_compound2 tc2
WHERE tc.CID = tc2.CID;
INSERT INTO ${SCHEMA}.compound (cid, cansmi, isosmi) SELECT CID, SMILES, ISOMERIC_SMILES FROM temp_compound;
DROP TABLE temp_compound;
DROP TABLE temp_compound2;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.compound IS 'From ${CPD_TSV_PATH} via ${HIERS_SCRIPT}, annotate_db_assaystats.py.'"
echo "Loaded compound table."


# Step 3c) Load CID to SID relations
CID2SID_TSV_FILE="pc_mlsmr_sid2cid.csv"
CID2SID_TSV_PATH="$DATA_DIR/$CID2SID_TSV_FILE"
psql -h $DB_HOST -d $DB_NAME <<EOF
-- CID has type TEXT so we can filter out "<NA>" values w/o error
-- (for some PubChem AID entries, certain SIDs do not have an associated CID)
-- (e.g., AID=651640 and SID=143391837)
CREATE TEMP TABLE temp_sub2cpd (
    SID INTEGER NOT NULL,
    CID TEXT
);

-- Copy data into the staging table
\COPY temp_sub2cpd (SID, CID) FROM '$CID2SID_TSV_PATH' WITH (FORMAT CSV, DELIMITER ',', HEADER true);

-- Remove rows with '<NA>' in CID and insert into the final table
INSERT INTO ${SCHEMA}.sub2cpd (sid, cid)
SELECT DISTINCT ON (sid) sid, cid::INTEGER
FROM temp_sub2cpd
WHERE CID <> '<NA>'
ORDER BY sid, cid
ON CONFLICT (sid) DO NOTHING;

-- Drop the staging table
DROP TABLE temp_sub2cpd;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.sub2cpd IS 'From ${CID2SID_TSV_PATH}.'"
echo "Loaded sub2cpd table."


# Step 4) Load assay-substance activities.
ASSAYSUB_TSV_FILE="pc_mlsmr_mlp_assaystats_act.csv"
ASSAYSUB_TSV_PATH="$DATA_DIR/$ASSAYSUB_TSV_FILE"
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_activity (
    AID INTEGER,
    SID INTEGER,
    ACTIVITY_OUTCOME INTEGER
);
\COPY temp_activity (AID, SID, ACTIVITY_OUTCOME) FROM '$ASSAYSUB_TSV_PATH' WITH (FORMAT CSV, DELIMITER ',', HEADER true);
INSERT INTO ${SCHEMA}.activity (aid, sid, outcome) SELECT AID, SID, ACTIVITY_OUTCOME FROM temp_activity;
DROP TABLE temp_activity;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.activity IS 'From: ${ASSAYSUB_TSV_PATH} (PubChem-FTP).'"
echo "Loaded activity table."