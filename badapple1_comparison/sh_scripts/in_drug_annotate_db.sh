# Author: Jack Ringer
# Date: 8/15/2024
# Description:
# Create labels for 'in_drug' column of badapple_comparison using drugcentral DB.

DB_NAME="badapple_comparison"
DB_USR="<your_usr>"
DB_PW="<your_password>"


# path to directory where all input CSV files stored
DATA_DIR="/media/jack/big_disk/data/badapple/badapple1_inputs"

# path to directory of this repo (Badapple2)
REPO_DIR="/home/jack/unm_gra/Badapple2"
# make working dir to call scripts
cd $REPO_DIR

DB_NAME="badapple_comparison"
SCHEMA="public"

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
python src/generate_scaffolds.py --log_fname $LOG_FILE --idelim ' ' --i $IFILE --max_rings 5 --o_mol $O_MOL --o_scaf $O_SCAF --o_mol2scaf $O_MOL2SCAF --smiles_column 0 --name_column 0
echo "Done generating scaffolds from ${IFILE}"

# Step 2) Load in_drug scaffold annotations.
python src/annotate_db_in_drug.py --dbname $DB_NAME --user $DB_USR --password $DB_PW  --scaf_file_path $O_SCAF
echo "in_drug annotations loaded into ${DB_NAME}"