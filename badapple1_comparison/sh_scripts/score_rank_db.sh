# Author: Jack Ringer
# Date: 8/15/2024
# Description:
# Generate scaffold scores + rankings using badapple formula.

DB_NAME="badapple_comparison"
DB_HOST="localhost"
SCHEMA="public"
ASSAY_ID_TAG="aid"
DB_USR="jack"
DB_PW="Fletcher12"

# path to directory where all input CSV files stored
DATA_DIR="/media/jack/big_disk/data/badapple/badapple1_inputs"

# path to directory of this repo (Badapple2)
REPO_DIR="/home/jack/unm_gra/Badapple2"
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
DBCOMMENT='Badapple Db (MLSMR compounds, PubChem HTS assays w/ 20k+ compounds)'
psql -d $DB_NAME -c "COMMENT ON DATABASE ${DB_NAME} IS '$DBCOMMENT'"
bash ./badapple1_comparison/sh_scripts/metadata_update.sh $DB_NAME $SCHEMA $ASSAY_ID_FILE "$DBCOMMENT"

# Step 2a) Annotate scaffold table with computed scores, add column "pscore".
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN IF NOT EXISTS pscore FLOAT NULL"
python src/scores_db_annotate.py \
	--host $DB_HOST \
	--dbname $DB_NAME \
	--schema $SCHEMA \
	--user $DB_USR \
	--pw $DB_PW \
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