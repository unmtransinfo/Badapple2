dir="/media/jack/big_disk/data/badapple"
aid_file="$dir/badapple_classic_tested_first10.aid"
out_json_file="$dir/aid2target_first10.json"
python3 src/pubchem_target_summaries.py --aid_file $aid_file \
    --out_json_file $out_json_file --fetch_uniprot_ids