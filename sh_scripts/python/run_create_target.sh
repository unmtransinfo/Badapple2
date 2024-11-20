# use 'run_protein_families.sh' BEFORE using this script
in_dir="/media/jack/big_disk/data/badapple/badapple2/assays"
o_dir="/media/jack/big_disk/data/badapple/badapple2/"
fam_table_fname="$in_dir/unique_target_consistent_fam.tsv"
final_table_fname="$o_dir/target.tsv"
python3 src/create_target.py \
    --inp_tsv $fam_table_fname \
    --out_tsv $final_table_fname