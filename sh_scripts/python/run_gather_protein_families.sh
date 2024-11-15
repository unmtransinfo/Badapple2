# use "run_pubchem_target_summaries.sh" BEFORE running this script
dir="/media/jack/big_disk/data/badapple/badapple2/assays"
out_json_file="$dir/aid2target_hts_20000.json"
tsv_file="$dir/aid2target_hts_20000.tsv" # intermediary file
tsv_fam_file="$dir/aid2target_hts_20000_fam.tsv" # final output

# convert json to tsv
python src/utils/json_to_tsv.py $out_json_file $tsv_file targets

# get families
python3 src/gather_protein_families.py $tsv_file $tsv_fam_file