dir="/media/jack/big_disk/data/badapple/badapple2/assays"
aid_file="$dir/assay_set.aid"
out_json_file="$dir/aid2target_hts_20000.json"
python3 src/pubchem_target_summaries.py --aid_file $aid_file \
    --out_json_file $out_json_file --fetch_uniprot_ids