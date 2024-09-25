dir="/home/jack/unm_gra/tmp/dtra"
input_tsv="${dir}/vendor_compounds.tsv"
output_tsv="${dir}/vendor_compounds_scores_badapple.tsv"
python3 src/api_scripts/api_get_compound_scores.py \
    --input_tsv "$input_tsv" \
    --output_tsv "$output_tsv"