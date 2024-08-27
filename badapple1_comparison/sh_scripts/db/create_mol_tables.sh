# Author: Jack Ringer
# Date: 8/27/2024
# Description:
# Create mol tables for structural searching using RDKit cartridge. Canonicalize SMILES.

if [ $# -lt 4 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA REPO_DIR\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3
REPO_DIR=$4


# Step 1) RDKit configuration.
psql -h $DB_HOST -d $DB_NAME -c 'CREATE EXTENSION IF NOT EXISTS rdkit'

### Step 1a) compound -> mols.
### Create mols table for RDKit structural searching.
cd $REPO_DIR
psql -h $DB_HOST -d $DB_NAME -f src/sql/create_rdkit_mols_table.sql
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.mols IS 'Compound structures. For RDKit structural searching.'"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX molidx ON ${SCHEMA}.mols USING gist(mol)"
psql -h $DB_HOST -d $DB_NAME -c "UPDATE ${SCHEMA}.compound SET cansmi = mol_to_smiles(mols.mol) FROM ${SCHEMA}.mols WHERE compound.cid = mols.cid"
echo "Loaded mols table."


### Step 1b) Create mols_scaf table for RDKit structural searching + canonicalize scaffold smiles.
### For database use and efficiency, although the smiles were canonicalized
### previously during scaffold analysis process.  Must be consistent
### between query and db.

psql -h $DB_HOST -d $DB_NAME -f src/sql/create_rdkit_mols_scaf_table.sql
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.mols_scaf IS 'Scaffold structures. For RDKit structural searching.'"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX molscafidx ON ${SCHEMA}.mols_scaf USING gist(scafmol)"
psql -q -h $DB_HOST -d $DB_NAME -c "UPDATE ${SCHEMA}.scaffold SET scafsmi = mol_to_smiles(mols_scaf.scafmol) FROM ${SCHEMA}.mols_scaf WHERE mols_scaf.id = scaffold.id"
echo "Loaded mols_scaf table."