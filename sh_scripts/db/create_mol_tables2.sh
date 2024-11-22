# Author: Jack Ringer
# Date: 11/24/2024
# Description:
# Create mol tables for structural searching using RDKit cartridge. 
# + Canonicalize SMILES across "compound", "scaffold", and "drug" tables
# (I believe canonicalization is redundant since we already generated canonical SMILES via RDKit,
# but we are ensuring that the DB using the RDKit cartridge's version of canon SMILES rather
# than the RDKit Python version of canon SMILES)

if [ $# -lt 4 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA REPO_DIR\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3
REPO_DIR=$4

cd $REPO_DIR

# create mol tables for "compound" and "scaffold"
bash badapple1_comparison/sh_scripts/db/create_mol_tables.sh $DB_NAME $DB_HOST $SCHEMA $REPO_DIR

# create mol table for "drug"
psql -h $DB_HOST -d $DB_NAME -f src/sql/create_rdkit_mols_drug_table.sql
psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON TABLE ${SCHEMA}.mols_drug IS 'Drug structures. For RDKit structural searching.'"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX moldrugidx ON ${SCHEMA}.mols_drug USING gist(mol)"
psql -q -h $DB_HOST -d $DB_NAME -c "UPDATE ${SCHEMA}.drug SET cansmi = mol_to_smiles(mols_drug.mol) FROM ${SCHEMA}.mols_drug WHERE mols_drug.drug_id = drug.drug_id"
echo "Loaded mols_drug table."



