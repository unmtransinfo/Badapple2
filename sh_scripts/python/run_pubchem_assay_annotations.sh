dir="/media/jack/big_disk/data/badapple"
aid_file="$dir/badapple_classic_tested_first10.aid"
out_json_file="$dir/assay_annotations_first10.json"
python3 src/pubchem_assay_annotations.py --aid_file $aid_file \
    --out_json_file $out_json_file