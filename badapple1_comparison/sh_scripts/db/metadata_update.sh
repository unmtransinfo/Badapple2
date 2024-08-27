# Author: Jack Ringer
# Date: 8/26/2024
# Description:
# Update metadata table in badapple DB.
# Based on: https://github.com/unmtransinfo/Badapple/blob/master/sh/Go_badapple_DbMetadata_update.sh
if [ $# -lt 4 ]; then
	printf "Syntax: %s DB_NAME SCHEMA ASSAY_ID_FILE COMMENT\n" $0
	exit
fi

DB_NAME=$1
SCHEMA=$2
ASSAY_ID_FILE=$3
COMMENT=$4
n_ass=`cat $ASSAY_ID_FILE | wc -l`
psql -d $DB_NAME -c "DELETE FROM $SCHEMA.metadata"
psql -d $DB_NAME -c "INSERT INTO $SCHEMA.metadata (db_description) VALUES ('${COMMENT}')"
psql -d $DB_NAME -c "UPDATE $SCHEMA.metadata SET db_date_built = CURRENT_TIMESTAMP"
psql -d $DB_NAME -c "UPDATE $SCHEMA.metadata SET median_ncpd_tested = (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ncpd_tested) FROM $SCHEMA.scaffold)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.metadata SET median_nsub_tested = (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nsub_tested) FROM $SCHEMA.scaffold)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.metadata SET median_nass_tested = (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nass_tested) FROM $SCHEMA.scaffold)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.metadata SET median_nsam_tested = (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY nsam_tested) FROM $SCHEMA.scaffold)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.metadata SET nass_total=$n_ass"