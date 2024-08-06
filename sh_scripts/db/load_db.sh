# author Jack Ringer
# Date: 7/29/2024
# Description:
# Load data into badapple2 DB
# based on: https://github.com/unmtransinfo/Badapple/blob/ae50bb04a58752933a807170b3d79c8906221500/sh/Go_badapple_DbLoad.sh

# run create_db.sh BEFORE running this script

# tip: run export PGPASSWORD=<your_pw> before running this script to avoid psql prompts for pw
DB_NAME="badapple2"
DB_HOST="localhost"
SCHEMA="public"
ASSAY_ID_TAG="aid"

# for DB comments
HIERS_SCRIPT="generate_scaffolds.py"
PUBCHEM_SCRIPT="pubchem_assays_local.py"

# path to directory of this repo (Badapple2)
REPO_DIR="/home/jack/unm_gra/Badapple2"
# make working dir to call scripts
cd $REPO_DIR

# path to directory where all input TSV files stored
DATA_DIR="/media/jack/big_disk/data/badapple2"

# NOTE 1: using temp tables in psql commands to rename/drop columns from input TSVs
# NOTE 2: it is assumed that SMILES for compounds/scaffolds are canonical
#   (This is true if using output from ${HIERS_SCRIPT})


# Step 1) Load scafs with scafids + scaf2scaf relationship
# expects SCAF_TSV_FILE to have header: scaffold_id smiles  hierarchy   scaf2scaf (TSV-separated)
# (output from ${HIERS_SCRIPT})
SCAF_TSV_FILE="scafs.tsv"
SCAF_TSV_PATH="$DATA_DIR/$SCAF_TSV_FILE"
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_scaf (
    scaffold_id INTEGER PRIMARY KEY,
    smiles VARCHAR(512) NOT NULL,
    hierarchy INTEGER,
    scaf2scaf VARCHAR(2048)
);
\COPY temp_scaf (scaffold_id, smiles, hierarchy, scaf2scaf) FROM '$SCAF_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
INSERT INTO ${SCHEMA}.scaffold (id, scafsmi, scaftree) SELECT scaffold_id, smiles, scaf2scaf FROM temp_scaf;
DROP TABLE temp_scaf;
EOF
psql -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.scaffold IS 'Scaffold definitions from HierS, see ${HIERS_SCRIPT}. Input file is ${SCAF_TSV_PATH}'"
echo "Loaded scafs table."


# Step 2) Load scaf2scaf table, uses "scaftree" column from "scaffold" table
SCAF2SCAF_SCRIPT="src/sql/fill_scaf2scaf.sql"
psql -h $DB_HOST -d $DB_NAME -f $SCAF2SCAF_SCRIPT
psql -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.scaf2scaf IS 'Scaffold parentage from scaftree column in scaffold table, see ${SCAF2SCAF_SCRIPT}.'"
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
psql -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.scaf2cpd IS 'From ${SCAF2CPD_TSV_PATH} via ${HIERS_SCRIPT}.'"
echo "Loaded scaf2cpd table."


# Step 3b) Load compounds with CIDs
# expects input tsv to have header: mol_id	smiles	isomeric_smiles	mol_name
# (output from ${HIERS_SCRIPT})
CPD_TSV_FILE="cpds.tsv"
CPD_TSV_PATH="$DATA_DIR/$CPD_TSV_FILE"
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_compound (
    mol_id INTEGER PRIMARY KEY,
    smiles VARCHAR(512) NOT NULL,
    isomeric_smiles VARCHAR(512) NOT NULL,
    mol_name INTEGER NOT NULL
);
\COPY temp_compound (mol_id, smiles, isomeric_smiles, mol_name) FROM '$CPD_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
INSERT INTO ${SCHEMA}.compound (cid, cansmi, isosmi) SELECT mol_name, smiles, isomeric_smiles FROM temp_compound;
DROP TABLE temp_compound;
EOF
psql -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.compound IS 'From ${CPD_TSV_PATH} via ${HIERS_SCRIPT}, badapple_assaystats_db_annotate.py.'"
echo "Loaded compound table."


# Step 3c) Load CID to SID relations
# (output from ${PUBCHEM_SCRIPT})
CID2SID_TSV_FILE="sid2cid.tsv"
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
psql -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.sub2cpd IS 'From ${CID2SID_TSV_PATH}, from PubChem (see ${PUBCHEM_SCRIPT}).'"
echo "Loaded sub2cpd table."


# Step 4) Load assay-substance activities.
ASSAYSUB_TSV_FILE="assaystats.tsv"
ASSAYSUB_TSV_PATH="$DATA_DIR/$ASSAYSUB_TSV_FILE"
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TEMP TABLE temp_activity (
    AID INTEGER,
    SID INTEGER,
    ACTIVITY_OUTCOME INTEGER
);
\COPY temp_activity (AID, SID, ACTIVITY_OUTCOME) FROM '$ASSAYSUB_TSV_PATH' WITH (FORMAT CSV, DELIMITER E'\t', HEADER true);
INSERT INTO ${SCHEMA}.activity (aid, sid, outcome) SELECT AID, SID, ACTIVITY_OUTCOME FROM temp_activity;
DROP TABLE temp_activity;
EOF
psql -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.activity IS 'From: ${ASSAYSUB_TSV_PATH} (PubChem-FTP), ${PUBCHEM_SCRIPT}.'"
echo "Loaded activity table."



# Step 5) RDKit configuration.
# sudo -u postgres psql -d $DB_NAME -c 'CREATE EXTENSION rdkit'

### Step 5a) compound -> mols.
### Create mols table for RDKit structural searching.
psql -d $DB_NAME -f src/sql/create_rdkit_mols_table.sql
psql -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.mols IS 'Compound structures. For RDKit structural searching.'"
psql -d $DB_NAME -c "CREATE INDEX molidx ON ${SCHEMA}.mols USING gist(mol)"
psql -d $DB_NAME -c "UPDATE ${SCHEMA}.compound SET cansmi = mol_to_smiles(mols.mol) FROM ${SCHEMA}.mols WHERE compound.cid = mols.cid"
echo "Loaded mols table."


### Step 5b) Canonicalize scaffold smiles.
### For database use and efficiency, although the smiles were canonicalized
### previously during scaffold analysis process.  Must be consistent
### between query and db.

### Create mols_scaf table for RDKit structural searching.
psql -d $DB_NAME -f src/sql/create_rdkit_mols_scaf_table.sql
psql -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.mols_scaf IS 'Scaffold structures. For RDKit structural searching.'"
psql -d $DB_NAME -c "CREATE INDEX molscafidx ON ${SCHEMA}.mols_scaf USING gist(scafmol)"
psql -q -d $DB_NAME -c "UPDATE ${SCHEMA}.scaffold SET scafsmi = mol_to_smiles(mols_scaf.scafmol) FROM ${SCHEMA}.mols_scaf WHERE mols_scaf.id = scaffold.id"
echo "Loaded mols_scaf table."

# Step 6) Index tables.  Greatly improves search performance.
psql -d $DB_NAME -c "CREATE INDEX scaf_scafid_idx ON ${SCHEMA}.scaffold (id)"
psql -d $DB_NAME -c "CREATE INDEX scaf_smi_idx on ${SCHEMA}.scaffold (scafsmi)"
psql -d $DB_NAME -c "CREATE INDEX mols_scaf_scafid_idx ON ${SCHEMA}.mols_scaf (id)"
psql -d $DB_NAME -c "CREATE INDEX cpd_cid_idx ON ${SCHEMA}.compound (cid)"
psql -d $DB_NAME -c "CREATE INDEX mols_cid_idx ON ${SCHEMA}.mols (cid)"
psql -d $DB_NAME -c "CREATE INDEX scaf2cpd_scafid_idx ON ${SCHEMA}.scaf2cpd (scafid)"
psql -d $DB_NAME -c "CREATE INDEX scaf2cpd_cid_idx ON ${SCHEMA}.scaf2cpd (cid)"
psql -d $DB_NAME -c "CREATE INDEX sub2cpd_cid_idx ON ${SCHEMA}.sub2cpd (cid)"
psql -d $DB_NAME -c "CREATE INDEX sub2cpd_sid_idx ON ${SCHEMA}.sub2cpd (sid)"
psql -d $DB_NAME -c "CREATE INDEX act_sid_idx ON ${SCHEMA}.activity (sid)"
psql -d $DB_NAME -c "CREATE INDEX act_aid_idx ON ${SCHEMA}.activity (aid)"
echo "Finished indexing tables."
