# author: Jack Ringer
# Date: 8/6/2024
# Description:
# Reset tables in DB

DB_NAME="badapple2"
DB_HOST="localhost"
SCHEMA="public"

read -p "Are you sure you want to truncate all tables in the ${DB_NAME} database? This action cannot be undone. (yes/no): " confirm

if [[ $confirm == "yes" ]]; then
    psql -h $DB_HOST -d $DB_NAME <<EOF
-- Truncate all tables and reset sequences
TRUNCATE TABLE ${SCHEMA}.activity,
               ${SCHEMA}.sub2cpd,
               ${SCHEMA}.compound,
               ${SCHEMA}.scaf2cpd,
               ${SCHEMA}.scaf2scaf,
               ${SCHEMA}.scaffold,
               ${SCHEMA}.mols,
               ${SCHEMA}.mols_scaf
RESTART IDENTITY CASCADE;
-- Drop mols and mols_scaf
DROP TABLE mols;
DROP TABLE mols_scaf;
-- Drop indexes
DROP INDEX molidx;
DROP INDEX molscafidx;
DROP INDEX scaf_scafid_idx;
DROP INDEX scaf_smi_idx;
DROP INDEX mols_scaf_scafid_idx;
DROP INDEX cpd_cid_idx;
DROP INDEX mols_cid_idx;
DROP INDEX scaf2cpd_scafid_idx;
DROP INDEX scaf2cpd_cid_idx;
DROP INDEX sub2cpd_cid_idx;
DROP INDEX sub2cpd_sid_idx;
DROP INDEX act_sid_idx;
DROP INDEX act_aid_idx;
EOF

    echo "All tables have been truncated."
else
    echo "Operation cancelled."
fi