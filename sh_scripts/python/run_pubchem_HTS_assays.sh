bioassays_file="/media/jack/big_disk/data/pubchem/Bioassay/Extras/bioassays.tsv.gz"
n_compound_thresh=20000
data_source_category="NIH Initiatives"
aid_out_file="/media/jack/big_disk/data/badapple/assays/hts_${n_compound_thresh}_${data_source_category}.aid"
pubchem_data_sources_file="/media/jack/big_disk/data/badapple/assays/PubChemDataSources_all.csv"
log_fname="pubchem_HTS_assays.log"

python3 src/pubchem_HTS_assays.py \
    --bioassays_file "$bioassays_file" \
    --aid_out_file "$aid_out_file" \
    --n_compound_thresh "$n_compound_thresh" \
    --data_source_category "$data_source_category" \
    --pubchem_data_sources_file "$pubchem_data_sources_file" \
    --log_fname "$log_fname"