# use 'run_pubchem_assay_annotations.sh' and 'run_pubchem_assay_description.sh'
# BEFORE using this script
in_dir="/media/jack/big_disk/data/badapple/badapple2/assays"
out_dir="/media/jack/big_disk/data/badapple/badapple2/"
annotations_json_file="$in_dir/assay_annotations_hts_20000.json"
descriptions_json_file="$in_dir/assay_descriptions_hts_20000.json"
tsv_out_path="$out_dir/aid2descriptors.tsv"
python3 src/create_aid2descriptors.py \
    --annotations_json_file $annotations_json_file \
    --descriptions_json_file $descriptions_json_file \
    --tsv_out_path $tsv_out_path