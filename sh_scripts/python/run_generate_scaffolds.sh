inp="/media/jack/big_disk/data/badapple/badapple_compounds.tsv"
out_dir="/media/jack/big_disk/data/badapple2"
max_rings=5
o_scaf="$out_dir/scafs.tsv"
o_mol="$out_dir/cpds.tsv"
o_mol2scaf="$out_dir/scaf2cpd.tsv"
log_fname="$out_dir/gen_scaf.log"
python src/generate_scaffolds.py --log_fname $log_fname --i $inp --iheader --max_rings $max_rings --o_mol $o_mol --o_scaf $o_scaf --o_mol2scaf $o_mol2scaf --smiles_column 1 --name_column 0
