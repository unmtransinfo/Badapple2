# Author: Jack Ringer
# Date: 2/15/2025
# Description:
# This script clones the badapple2DB but annotates compounds & scaffolds using only the 823 original MLP bioassays.
# The purpose is to determine how much of an effect the updated substance records had on pScores vs the new 83 assay records in badapple2.

NEW_DB_NAME="badappleupdated"
DB_HOST="localhost"
SCHEMA="public"
ASSAY_ID_TAG="aid"
DB_USER="<your_usr>"
DB_PASSWORD="<your_pw>"
REPO_DIR="/home/jack/unm_gra/Badapple2"
AID_FILE="/home/jack/unm_gra/data/badapple/badapple1/badapple_tested.aid"
DATA_DIR="/home/jack/unm_gra/data/badapple/badappleupdated"
NASS_TESTED_MIN=50

# clone badapple2DB
bash clone_badapple2.sh $DB_USER $NEW_DB_NAME

# annotate compounds
bash ../annotate_compound_stats.sh $NEW_DB_NAME $DB_HOST $SCHEMA $ASSAY_ID_TAG $DB_USER $DB_PASSWORD $REPO_DIR $AID_FILE

# annotate scaffolds
bash ../annotate_scaffold_stats.sh $NEW_DB_NAME $DB_HOST $SCHEMA $ASSAY_ID_TAG $DB_USER $DB_PASSWORD $REPO_DIR $AID_FILE $NASS_TESTED_MIN


# annotate pScores
psql -d $NEW_DB_NAME -c "UPDATE $SCHEMA.scaffold SET pscore = NULL"
BADAPPLE_CLASSIC_MEDIAN_NCPD_TESTED=2
BADAPPLE_CLASSIC_MEDIAN_NSUB_TESTED=2
BADAPPLE_CLASSIC_MEDIAN_NASS_TESTED=634
BADAPPLE_CLASSIC_MEDIAN_NSAM_TESTED=773
bash ../annotate_scores2.sh $NEW_DB_NAME $DB_HOST $SCHEMA $ASSAY_ID_TAG $DB_USER $DB_PASSWORD $REPO_DIR $DATA_DIR "badapple2DB with score annotations from the original 823 MLP assays used in badapple_classic" $BADAPPLE_CLASSIC_MEDIAN_NCPD_TESTED $BADAPPLE_CLASSIC_MEDIAN_NSUB_TESTED $BADAPPLE_CLASSIC_MEDIAN_NASS_TESTED $BADAPPLE_CLASSIC_MEDIAN_NSAM_TESTED