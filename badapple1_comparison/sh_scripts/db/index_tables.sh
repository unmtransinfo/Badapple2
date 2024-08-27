# Author: Jack Ringer
# Date: 8/27/2024
# Description:
# Index tables in the DB to improve performance.

if [ $# -lt 3 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3

# index tables
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX scaf_scafid_idx ON ${SCHEMA}.scaffold (id)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX scaf_smi_idx on ${SCHEMA}.scaffold (scafsmi)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX mols_scaf_scafid_idx ON ${SCHEMA}.mols_scaf (id)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX cpd_cid_idx ON ${SCHEMA}.compound (cid)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX mols_cid_idx ON ${SCHEMA}.mols (cid)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX scaf2cpd_scafid_idx ON ${SCHEMA}.scaf2cpd (scafid)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX scaf2cpd_cid_idx ON ${SCHEMA}.scaf2cpd (cid)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX sub2cpd_cid_idx ON ${SCHEMA}.sub2cpd (cid)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX sub2cpd_sid_idx ON ${SCHEMA}.sub2cpd (sid)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX act_sid_idx ON ${SCHEMA}.activity (sid)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX act_aid_idx ON ${SCHEMA}.activity (aid)"
echo "Finished indexing tables."