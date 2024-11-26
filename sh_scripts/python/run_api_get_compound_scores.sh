dir="/home/jack/unm_gra/tmp/dtra"
input_tsv="${dir}/tsne2.csv"
output_tsv="${dir}/tsne2_badapple_scores.tsv"
python3 src/api_get_compound_scores.py \
    --input_tsv "$input_tsv" \
    --output_tsv "$output_tsv" \
    --idelim "," \
    --iheader \
    --smiles_column 3 \
    --name_column 2