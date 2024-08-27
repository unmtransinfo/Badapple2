# Author: Jack Ringer
# Date: 8/15/2024
# Description:
# Create labels for 'in_drug' column of badapple_comparison using drugcentral DB.

if [ $# -lt 8 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA ASSAY_ID_TAG DB_USER DB_PASSWORD REPO_DIR DATA_DIR\n" $0
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

# make working dir to call scripts
cd $REPO_DIR

# Step 1) Generate scaffold analysis of drug molecule file (IFILE)
# IFILE is currently from scp (in Badapple2 can use drugcentral DB to generate)
IFILE="${DATA_DIR}/drugcentral.smi"
PREFIX="${DATA_DIR}/drugcentral_hscaf"
LOG_FILE="${PREFIX}.log"
O_MOL="${PREFIX}_mol.tsv"
O_MOL2SCAF="${PREFIX}_mol2scaf.tsv"
O_SCAF="${PREFIX}_scaf.tsv"

NMOL=`cat $IFILE |wc -l`
echo "NMOL($IFILE) = $NMOL"

# don't provide name_column as it isn't unique
python src/generate_scaffolds.py --log_fname $LOG_FILE --idelim ' ' \
    --i $IFILE --max_rings 5 --o_mol $O_MOL --o_scaf $O_SCAF \
    --o_mol2scaf $O_MOL2SCAF --smiles_column 0 --name_column 0

echo "Done generating scaffolds from ${IFILE}"

# Step 2) Load in_drug scaffold annotations.
python src/annotate_db_in_drug.py --dbname $DB_NAME --user $DB_USER \
    --host $DB_HOST --dbschema $SCHEMA --password $DB_PASSWORD  --scaf_file_path $O_SCAF

echo "in_drug annotations loaded into ${DB_NAME}"