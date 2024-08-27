DB_NAME="badapple_comparison"
DB_HOST="localhost"
SCHEMA="public"
ASSAY_ID_TAG="aid"
DB_USR="<your_usr>"
DB_PW="<your_pw>"

# path to directory of this repo (Badapple2)
REPO_DIR="/home/jack/unm_gra/Badapple2"
cd $REPO_DIR

# Step 7) Generate compound activity statistics.  Populate/annotate
# compound table with calculated assay stats.
# (sTotal,sTested,sActive,aTested,aActive,wTested,wActive)
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.compound ADD COLUMN nsub_total INTEGER"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.compound ADD COLUMN nsub_tested INTEGER"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.compound ADD COLUMN nsub_active INTEGER"
psql -d $DB_NAME -c "UPDATE $SCHEMA.compound SET (nsub_total, nsub_tested, nsub_active)  = (NULL, NULL, NULL)"
python src/annotate_db_assaystats.py \
	--annotate_compounds \
	--assay_id_tag $ASSAY_ID_TAG \
	--host $DB_HOST \
	--dbname $DB_NAME \
	--schema $SCHEMA \
	--activity $SCHEMA \
	--user $DB_USR \
	--pw $DB_PW \
	--v

echo "Done annotating compounds."


# Step 8) Generate scaf activity statistics.  Populate/annotate scaffold table with calculated assay stats.
# Scaffold table must be ALTERed to contain activity statistics.
# (cTotal,cTested,cActive,sTotal,sTested,sActive,aTested,aActive,wTested,wActive)
#
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN ncpd_total INTEGER"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN ncpd_tested INTEGER"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN ncpd_active INTEGER"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (ncpd_total, ncpd_tested, ncpd_active)  = (NULL, NULL, NULL)"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN nsub_total INTEGER"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN nsub_tested INTEGER"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN nsub_active INTEGER"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (nsub_total, nsub_tested, nsub_active)  = (NULL, NULL, NULL)"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN nass_tested INTEGER"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN nass_active INTEGER"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (nass_tested, nass_active)  = (NULL, NULL)"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN nsam_tested INTEGER"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN nsam_active INTEGER"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET (nsam_tested, nsam_active)  = (NULL, NULL)"
psql -d $DB_NAME -c "ALTER TABLE $SCHEMA.scaffold ADD COLUMN in_drug BOOLEAN"
psql -d $DB_NAME -c "UPDATE $SCHEMA.scaffold SET in_drug  = NULL"

#(~5h but ~4h to 50%, since top scafs have more data.)
python src/annotate_db_assaystats.py \
	--annotate_scaffolds \
	--assay_id_tag $ASSAY_ID_TAG \
	--host $DB_HOST \
	--dbname $DB_NAME \
	--schema $SCHEMA \
	--activity $SCHEMA \
	--user $DB_USR \
	--pw $DB_PW \
	--v


echo "Done annotating scaffolds."