dir="/home/jack/unm_gra/tmp/dtra"
input_tsv="${dir}/tsne2_badapple_scores.tsv"
output_tsv="${dir}/tsne2_badapple_filter_result.tsv"
python3 src/apply_badapple_filter.py \
    --input_tsv "$input_tsv" \
    --output_tsv "$output_tsv" \
    --iheader \
    --smiles_column 1 \
    --name_column 2 \
    --pscore_column 7 \
    --inDrug_column 8 \
    --inDB_column 5