bioassays_file="/media/jack/big_disk/data/pubchem/Bioassay/Extras/bioassays.tsv.gz"
n_compound_thresh=20000
aid_out_file="/media/jack/big_disk/data/badapple/assays/hts_${n_compound_thresh}.aid"
log_fname="pubchem_HTS_assays.log"

python3 src/pubchem_HTS_assays.py \
    --bioassays_file "$bioassays_file" \
    --aid_out_file "$aid_out_file" \
    --n_compound_thresh "$n_compound_thresh" \
    --log_fname "$log_fname"