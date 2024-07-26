aid_file="/home/jack/unm_gra/Badapple2/data/badapple1/badapple_tested.aid"
zip_dir="/media/jack/big_disk/data/pubchem/bioassay"
o_dir="/media/jack/big_disk/data/badapple2"
o_sid2cid="${o_dir}/sid2cid.tsv"
o_assaystats="${o_dir}/assaystats.tsv"
python3 src/pubchem_assays_local.py --aid_file $aid_file \
    --zip_dir $zip_dir --o_sid2cid $o_sid2cid \
    --o_assaystats $o_assaystats
