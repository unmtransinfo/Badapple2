dir="/media/jack/big_disk/data/badapple"
aid_file="$dir/badapple_comparison_tested_first10.aid"
out_json_file="$dir/aid2target_first10.json"
python3 src/pubchem_target_summaries.py --aid_file $aid_file \
    --out_json_file $out_json_file