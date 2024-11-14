assay_zip_dir="/media/jack/big_disk/data/pubchem/Bioassay/CSV/Data"
o_dir="/media/jack/big_disk/data/badapple/badapple2"
aid_file="${o_dir}/assay_set.aid"
o_compound="${o_dir}/cpds_set.tsv"
o_sid2cid="${o_dir}/sid2cid.tsv"
o_assaystats="${o_dir}/assaystats.tsv"
python3 src/pubchem_assays_local.py --aid_file $aid_file \
    --assay_zip_dir $assay_zip_dir --o_compound $o_compound \
    --o_sid2cid $o_sid2cid --o_assaystats $o_assaystats
