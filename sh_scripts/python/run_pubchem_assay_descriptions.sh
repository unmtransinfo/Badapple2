dir="/media/jack/big_disk/data/badapple/badapple2/assays"
aid_file="$dir/assay_set.aid"
out_json_file="$dir/assay_descriptions_hts_20000.json"
python3 src/pubchem_assay_descriptions.py --aid_file $aid_file \
    --out_json_file $out_json_file