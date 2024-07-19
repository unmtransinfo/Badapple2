rd_mol="omol.tsv"
rd_scaf="oscaf.tsv"
rd_mol2scaf="omol2scaf.tsv"
ba_mol="/media/jack/big_disk/data/badapple/badapple_compounds.tsv"
ba_scaf="/media/jack/big_disk/data/badapple/badapple_scafs.tsv"
ba_mol2scaf="/media/jack/big_disk/data/badapple/scaf2cpd.tsv"
log_out="badapple_compare.out"
python3 compare_scaffolds.py --log_fname $log_out --rdkit_mol_tsv_file $rd_mol --badapple_mol_tsv_file $ba_mol --rdkit_scaf_tsv_file $rd_scaf --badapple_scaf_tsv_file $ba_scaf --rdkit_mol2scaf_tsv_file $rd_mol2scaf --badapple_mol2scaf_tsv_file $ba_mol2scaf
