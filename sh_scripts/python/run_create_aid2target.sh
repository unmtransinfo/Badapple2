# use "run_pubchem_target_summaries.sh" BEFORE running this script
in_dir="/media/jack/big_disk/data/badapple/badapple2/assays"
o_dir="/media/jack/big_disk/data/badapple/badapple2"
out_json_file="$in_dir/aid2target_hts_20000.json"
target_tsv_file="$in_dir/aid2target_hts_20000.tsv" # input


# convert json to tsv
python src/utils/json_to_tsv.py $out_json_file $target_tsv_file targets

# create aid2target table, get unique targets
target_table_fname="$in_dir/unique_target.tsv"
aid2target_table_fname="$o_dir/aid2target.tsv"
python3 src/create_aid2target.py --inp_tsv $target_tsv_file \
    --unique_target_out_path $target_table_fname \
    --aid2target_out_path $aid2target_table_fname