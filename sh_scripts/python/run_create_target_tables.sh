# use "run_gather_protein_families.sh" BEFORE running this script
in_dir="/media/jack/big_disk/data/badapple/badapple2/assays"
o_dir="/media/jack/big_disk/data/badapple/badapple2"
tsv_fam_file="$in_dir/aid2target_hts_20000_fam.tsv" # input
target_table_fname="$o_dir/target.tsv"
aid2target_table_fname="$o_dir/aid2target.tsv"
log_fname="$o_dir/create_target_tables.log"
python3 src/create_target_tables.py --inp_tsv $tsv_fam_file \
    --target_out_path $target_table_fname \
    --aid2target_out_path $aid2target_table_fname \
    --log_fname $log_fname