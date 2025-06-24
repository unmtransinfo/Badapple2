# Author: Jack Ringer
# Date: 11/22/2024
# Description:
# Generate scaffold scores + rankings using badapple formula for Badapple2 DB.

if [ $# -lt 12 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA ASSAY_ID_TAG DB_USER DB_PASSWORD REPO_DIR DATA_DIR DB_COMMENT BADAPPLE_CLASSIC_MEDIAN_NSUB_TESTED BADAPPLE_CLASSIC_MEDIAN_NASS_TESTED BADAPPLE_CLASSIC_MEDIAN_NSAM_TESTED\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3
ASSAY_ID_TAG=$4
DB_USER=$5
DB_PASSWORD=$6
REPO_DIR=$7
DATA_DIR=$8
DB_COMMENT=$9
BADAPPLE_CLASSIC_MEDIAN_NCPD_TESTED=${10}
BADAPPLE_CLASSIC_MEDIAN_NSUB_TESTED=${11}
BADAPPLE_CLASSIC_MEDIAN_NASS_TESTED=${12}
BADAPPLE_CLASSIC_MEDIAN_NSAM_TESTED=${13}

# make working dir to call scripts
cd $REPO_DIR

# Step 0) Generate assay id files
ASSAY_ID_FILE=$DATA_DIR/${DB_NAME}_tested.${ASSAY_ID_TAG}
psql -q --no-align -d $DB_NAME \
	-c "SELECT DISTINCT ${ASSAY_ID_TAG} FROM $SCHEMA.activity ORDER BY ${ASSAY_ID_TAG}" \
	|sed -e '1d' |sed -e '$d' \
	>$ASSAY_ID_FILE

ASSAY_ACTIVE_ID_FILE=$DATA_DIR/${DB_NAME}_active.${ASSAY_ID_TAG}
psql -q --no-align -d $DB_NAME \
	-c "SELECT DISTINCT ${ASSAY_ID_TAG} FROM $SCHEMA.activity WHERE outcome=2 ORDER BY ${ASSAY_ID_TAG}" \
	|sed -e '1d' |sed -e '$d' \
	>$ASSAY_ACTIVE_ID_FILE

# Step 1) Load metadata.  Postgres 9.4+
psql -d $DB_NAME -c "COMMENT ON DATABASE ${DB_NAME} IS '$DBCOMMENT'"
bash badapple1_comparison/sh_scripts/db/metadata_update.sh $DB_NAME $SCHEMA $ASSAY_ID_FILE "$DB_COMMENT"
psql -d $DB_NAME -c "UPDATE $SCHEMA.metadata SET median_ncpd_tested_classic = $BADAPPLE_CLASSIC_MEDIAN_NCPD_TESTED"
psql -d $DB_NAME -c "UPDATE $SCHEMA.metadata SET median_nsub_tested_classic = $BADAPPLE_CLASSIC_MEDIAN_NSUB_TESTED"
psql -d $DB_NAME -c "UPDATE $SCHEMA.metadata SET median_nass_tested_classic = $BADAPPLE_CLASSIC_MEDIAN_NASS_TESTED"
psql -d $DB_NAME -c "UPDATE $SCHEMA.metadata SET median_nsam_tested_classic = $BADAPPLE_CLASSIC_MEDIAN_NSAM_TESTED"

# Step 2a) Annotate scaffold table with computed scores, add column "pscore".
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN IF NOT EXISTS pscore FLOAT NULL"
psql -d "$DB_NAME" -c "UPDATE $SCHEMA.scaffold SET pscore = NULL;"
python src/annotate_db_scores.py \
	--badapple_version 2 \
	--host $DB_HOST \
	--dbname $DB_NAME \
	--dbschema $SCHEMA \
	--user $DB_USER \
	--password $DB_PASSWORD \
	-vvv

# Step 2b) Annotate scaffold table with score rank, add column "prank".
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN IF NOT EXISTS prank INT NULL"

# Sub-select needed else: "ERROR: cannot use window function in UPDATE"
psql -d $DB_NAME <<EOF
UPDATE $SCHEMA.scaffold s
SET prank = x.pr
FROM (
        SELECT id, rank() OVER (ORDER BY pscore DESC) AS pr
        FROM $SCHEMA.scaffold s2
        WHERE pscore IS NOT NULL
        ) AS x
WHERE s.id = x.id
AND s.pscore IS NOT NULL
        ;
EOF