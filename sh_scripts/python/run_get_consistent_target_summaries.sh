# use 'run_create_aid2target.sh' BEFORE this script
in_dir="/media/jack/big_disk/data/badapple/badapple2/assays"
target_table_fname="$in_dir/unique_target.tsv"
consistent_table_fname="$in_dir/unique_target_consistent.tsv"
python3 src/get_consistent_target_summaries.py \
    --input_tsv $target_table_fname \
    --out_tsv $consistent_table_fname