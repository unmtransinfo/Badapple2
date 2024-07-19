inp="/media/jack/big_disk/data/badapple/badapple_compounds.tsv"
max_rings=30
o_scaf="oscaf.tsv"
o_mol="omol.tsv"
o_mol2scaf="omol2scaf.tsv"
log_fname="gen_scaf_log.out"
python generate_scaffolds.py --log_fname $log_fname --i $inp --iheader --max_rings $max_rings --o_mol $o_mol --o_scaf $o_scaf --o_mol2scaf $o_mol2scaf --smiles_column 1 --name_column 0
