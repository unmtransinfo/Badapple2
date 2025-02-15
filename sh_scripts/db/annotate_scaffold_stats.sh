# Author: Jack Ringer
# Date: 11/22/2024
# Description:
# Annotate scaffold table with activity stats for Badapple2.
# NOTE: This process can take several hours!

if [ $# -lt 7 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA ASSAY_ID_TAG DB_USER DB_PASSWORD REPO_DIR\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3
ASSAY_ID_TAG=$4
DB_USER=$5
DB_PASSWORD=$6
REPO_DIR=$7
AID_FILE=${8:-"")} # optional

# cd to run scripts using relative path
cd $REPO_DIR


# Step 2) Generate scaf activity statistics.  Populate/annotate scaffold table with calculated assay stats.
# Scaffold table must be ALTERed to contain activity statistics.
# (cTotal,cTested,cActive,sTotal,sTested,sActive,aTested,aActive,wTested,wActive)
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (ncpd_total, ncpd_tested, ncpd_active)  = (NULL, NULL, NULL)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (nsub_total, nsub_tested, nsub_active)  = (NULL, NULL, NULL)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (nass_tested, nass_active)  = (NULL, NULL)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (nsam_tested, nsam_active)  = (NULL, NULL)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET in_drug  = NULL"
psql -d $DB_NAME -c "TRUNCATE TABLE $SCHEMA.scaf2activeaid" # this is in case we're re-rerunning the workflow

python src/annotate_db_assaystats.py \
	--annotate_scaffolds \
	--assay_id_tag $ASSAY_ID_TAG \
	--host $DB_HOST \
	--dbname $DB_NAME \
	--schema $SCHEMA \
	--activity $SCHEMA \
	--user $DB_USER \
	--password $DB_PASSWORD \
	--aid_file $AID_FILE \
	--v \
	--write_scafid2activeaid

echo "Done annotating scaffolds."