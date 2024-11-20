# use 'run_get_consistent_target_summaries.sh' BEFORE using this script
in_dir="/media/jack/big_disk/data/badapple/badapple2/assays"
consistent_table_fname="$in_dir/unique_target_consistent.tsv"
fam_table_fname="$in_dir/unique_target_consistent_fam.tsv"
python3 src/get_protein_families.py $consistent_table_fname $fam_table_fname