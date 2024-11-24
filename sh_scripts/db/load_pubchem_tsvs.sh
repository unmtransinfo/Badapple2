# Author: Jack Ringer
# Date: 11/21/2024
# Description:
# Load TSV files generated from PubChem data into DB.
# I realize this script is extremely similar to load_csv_files.sh and they
# perhaps could be combined into a single script, but since each of these
# files are likely only ever going to be run once is it really worth it?

if [ $# -lt 12 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA SCAF_TSV_PATH SCAF2CPD_TSV_PATH BIOACTIVITY_CPD_SET_TSV_PATH CPD_TSV_PATH CID2SID_TSV_PATH ACTIVITY_TSV_PATH AID2DESCRIPTORS_TSV_PATH TARGET_TSV_PATH AID2TARGET_TSV_PATH REPO_DIR\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3
SCAF_TSV_PATH=$4
SCAF2CPD_TSV_PATH=$5
BIOACTIVITY_CPD_SET_TSV_PATH=$6 # from pubchem_assay_target_summaries.py
CPD_TSV_PATH=$7 # from generate_scaffolds.py
CID2SID_TSV_PATH=$8
ACTIVITY_TSV_PATH=$9
AID2DESCRIPTORS_TSV_PATH=${10}
TARGET_TSV_PATH=${11}
AID2TARGET_TSV_PATH=${12}
REPO_DIR=${13}

# NOTE: using temp tables in psql commands to rename/drop columns from input TSVs

# for DB comments
HIERS_SCRIPT="generate_scaffolds.py"

# Step 1) Load scafs with scafids + scaf2scaf relationship
# expects file at SCAF_TSV_PATH to have header: scaffold_id	canon_smiles	kekule_smiles	hierarchy	scaf2scaf (TSV-separated)
# (output from ${HIERS_SCRIPT})
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
SCAF2SCAF_SCRIPT="$REPO_DIR/src/sql/fill_scaf2scaf.sql"
psql -h $DB_HOST -d $DB_NAME -f $SCAF2SCAF_SCRIPT
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.scaf2scaf IS 'Scaffold parentage from scaftree column in scaffold table, see ${SCAF2SCAF_SCRIPT}.'"
echo "Loaded scaf2scaf table."


# Step 3a) Load scaf2cpd links
# expects input tsv to have header: mol_id	mol_name	scaffold_id
# will be using mol_name as CID (original "names" given to mols was CID, mol_id is just from counting)
# (output from ${HIERS_SCRIPT})
psql -h $DB_HOST -d $DB_NAME <<EOF
-- have to use additional staging tables because in some extreme edge cases
-- CID is not included in the PubChem assay record even though SMILES are
-- these entries (where CID is <NA>) are removed before being passed to the compound table
CREATE TEMP TABLE staging_temp_compound (
    CID TEXT,
    SMILES VARCHAR(2048),
    ISOMERIC_SMILES VARCHAR(2048) NOT NULL
);

CREATE TEMP TABLE staging_temp_compound2 (
    mol_id INTEGER PRIMARY KEY,
    SMILES VARCHAR(2048) NOT NULL,
    CID TEXT
);
\COPY staging_temp_compound (CID, ISOMERIC_SMILES) FROM '$BIOACTIVITY_CPD_SET_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
\COPY staging_temp_compound2 (mol_id, SMILES, CID) FROM '$CPD_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);

CREATE TEMP TABLE temp_compound AS
SELECT
    CAST(CID AS INTEGER) AS CID,
    SMILES,
    ISOMERIC_SMILES
FROM
    staging_temp_compound
WHERE
    CID != '<NA>';

CREATE TEMP TABLE temp_compound2 AS
SELECT
    mol_id,
    SMILES,
    CAST(CID AS INTEGER) AS CID
FROM
    staging_temp_compound2
WHERE
    CID != '<NA>';

-- add canonical (non-isomeric) SMILES from rdkit into temp_compound table
UPDATE temp_compound tc
SET SMILES = tc2.SMILES
FROM temp_compound2 tc2
WHERE tc.CID = tc2.CID;

-- this is for the compound with CID 28117 and (invalid) SMILES "F[Si-2](F)(F)(F)(F)F"
DELETE FROM temp_compound
WHERE SMILES IS NULL;

INSERT INTO ${SCHEMA}.compound (cid, cansmi, isosmi) SELECT CID, SMILES, ISOMERIC_SMILES FROM temp_compound;

DROP TABLE temp_compound;
DROP TABLE temp_compound2;
DROP TABLE staging_temp_compound;
DROP TABLE staging_temp_compound2;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.compound IS 'From ${BIOACTIVITY_CPD_SET_TSV_PATH} via ${HIERS_SCRIPT}, annotate_db_assaystats.py.'"
echo "Loaded compound table."


# Step 3c) Load CID to SID relations
psql -h $DB_HOST -d $DB_NAME <<EOF
-- CID has type TEXT so we can filter out "<NA>" values w/o error
-- (for some PubChem AID entries, certain SIDs do not have an associated CID)
-- (e.g., AID=651640 and SID=143391837)
CREATE TEMP TABLE temp_sub2cpd (
    SID INTEGER NOT NULL,
    CID TEXT
);

-- Copy data into the staging table
\COPY temp_sub2cpd (SID, CID) FROM '$CID2SID_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);

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
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_activity (
    AID INTEGER,
    SID INTEGER,
    ACTIVITY_OUTCOME INTEGER
);
\COPY temp_activity (AID, SID, ACTIVITY_OUTCOME) FROM '$ACTIVITY_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
INSERT INTO ${SCHEMA}.activity (aid, sid, outcome) SELECT AID, SID, ACTIVITY_OUTCOME FROM temp_activity;
DROP TABLE temp_activity;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.activity IS 'From: ${ACTIVITY_TSV_PATH} (PubChem-FTP).'"
echo "Loaded activity table."


# Step 5) Load assay descriptors file
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_aid2desc (
    aid INTEGER PRIMARY KEY,
	description TEXT NOT NULL,
	protocol TEXT NOT NULL,
	assay_format VARCHAR(128),
	assay_type VARCHAR(128),
	detection_method VARCHAR(128)
);
\COPY temp_aid2desc (aid, description, protocol, assay_format, assay_type, detection_method) FROM '$AID2DESCRIPTORS_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
INSERT INTO ${SCHEMA}.aid2descriptors (aid, description, protocol, assay_format, assay_type, detection_method) SELECT aid, description, protocol, assay_format, assay_type, detection_method FROM temp_aid2desc;
DROP TABLE temp_aid2desc;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.aid2descriptors IS 'From: ${AID2DESCRIPTORS_TSV_PATH} (PubChem).'"
echo "Loaded aid2descriptors table."


# Step 6) Load target table
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_target (
	target_id INTEGER PRIMARY KEY,
	type VARCHAR(64) NOT NULL,
	external_id VARCHAR(64) NOT NULL,
	external_id_type VARCHAR(64) NOT NULL,
	name VARCHAR(256),
	taxonomy VARCHAR(128),
	taxonomy_id INTEGER,
	protein_family VARCHAR(64)
	);
\COPY temp_target (target_id, type, external_id, external_id_type, name, taxonomy, taxonomy_id, protein_family) FROM '$TARGET_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
INSERT INTO ${SCHEMA}.target (target_id, type, external_id, external_id_type, name, taxonomy, taxonomy_id, protein_family) SELECT target_id, type, external_id, external_id_type, name, taxonomy, taxonomy_id, protein_family FROM temp_target;
DROP TABLE temp_target;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.target IS 'From: ${TARGET_TSV_PATH} (PubChem).'"
echo "Loaded target table."


# Step 7) Load aid2target table
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_aid2target (
	aid INTEGER NOT NULL,
    target_id INTEGER NOT NULL
	);
\COPY temp_aid2target (aid, target_id) FROM '$AID2TARGET_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
INSERT INTO ${SCHEMA}.aid2target (aid, target_id) SELECT aid, target_id FROM temp_aid2target;
DROP TABLE temp_aid2target;
EOF
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.target IS 'From: ${AID2TARGET_TSV_PATH} (PubChem).'"
echo "Loaded aid2target table."