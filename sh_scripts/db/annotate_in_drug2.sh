# Author: Jack Ringer
# Date: 11/22/2024
# Description:
# Create labels for 'in_drug' column of Badapple 2.0 using drugcentral data.
# This script is simpler than the from "badapple_classic" because
# we now have the "scaf2drug" table

if [ $# -lt 8 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA ASSAY_ID_TAG DB_USER DB_PASSWORD REPO_DIR DATA_DIR\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3

psql -h $DB_HOST -d $DB_NAME <<EOF
UPDATE ${SCHEMA}.scaffold
SET in_drug = CASE
    WHEN id IN (SELECT scafid FROM ${SCHEMA}.scaf2drug) THEN true
    ELSE false
END;
EOF

echo "in_drug annotations loaded into ${DB_NAME}"