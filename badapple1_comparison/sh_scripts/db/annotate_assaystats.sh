# Author: Jack Ringer
# Date: 8/27/2024
# Description:
# Annotate compound and scaffold tables with activity stats. 
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

# cd to run scripts using relative path
cd $REPO_DIR

# Step 1) Generate compound activity statistics.  Populate/annotate
# compound table with calculated assay stats.
# (sTotal,sTested,sActive,aTested,aActive,wTested,wActive)
psql -d $DB_NAME -c "UPDATE $SCHEMA.compound SET (nsub_total, nsub_tested, nsub_active)  = (NULL, NULL, NULL)"
python src/annotate_db_assaystats.py \
	--annotate_compounds \
	--assay_id_tag $ASSAY_ID_TAG \
	--host $DB_HOST \
	--dbname $DB_NAME \
	--schema $SCHEMA \
	--activity $SCHEMA \
	--user $DB_USER \
	--password $DB_PASSWORD \
	--v

echo "Done annotating compounds."


# Step 2) Generate scaf activity statistics.  Populate/annotate scaffold table with calculated assay stats.
# Scaffold table must be ALTERed to contain activity statistics.
# (cTotal,cTested,cActive,sTotal,sTested,sActive,aTested,aActive,wTested,wActive)
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (ncpd_total, ncpd_tested, ncpd_active)  = (NULL, NULL, NULL)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (nsub_total, nsub_tested, nsub_active)  = (NULL, NULL, NULL)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (nass_tested, nass_active)  = (NULL, NULL)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (nsam_tested, nsam_active)  = (NULL, NULL)"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET in_drug  = NULL"


python src/annotate_db_assaystats.py \
	--annotate_scaffolds \
	--assay_id_tag $ASSAY_ID_TAG \
	--host $DB_HOST \
	--dbname $DB_NAME \
	--schema $SCHEMA \
	--activity $SCHEMA \
	--user $DB_USER \
	--password $DB_PASSWORD \
	--v

echo "Done annotating scaffolds."