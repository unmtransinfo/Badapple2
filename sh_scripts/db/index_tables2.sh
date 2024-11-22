# Author: Jack Ringer
# Date: 11/22/2024
# Description:
# Index tables which are new to Badapple 2.0

if [ $# -lt 3 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3

# index tables unique to Badapple 2.0
# NOTE: don't need to index columns marked primary key
# aid2target
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX aid2target_aid_idx ON ${SCHEMA}.aid2target (aid)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX aid2target_target_id_idx ON ${SCHEMA}.aid2target (target_id)"
# mols_drug
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX mols_drug_drug_id_idx ON ${SCHEMA}.mols_drug (drug_id)"
# scaf2drug
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX scaf2drug_scafid_idx ON ${SCHEMA}.scaf2drug (scafid)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX scaf2drug_drug_id_idx ON ${SCHEMA}.scaf2drug (drug_id)"
# scaf2activeaid
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX scaf2activeaid_scafid_idx ON ${SCHEMA}.scaf2activeaid (scafid)"
psql -h $DB_HOST -d $DB_NAME -c "CREATE INDEX scaf2activeaid_aid_idx ON ${SCHEMA}.scaf2activeaid (aid)"

echo "Finished indexing tables."