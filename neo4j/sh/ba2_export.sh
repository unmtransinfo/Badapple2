#!/bin/bash
###
# Export Badapple2 Pg db to TSVs for Neo4j build.
#
DBHOST="localhost"
DBPORT="5443"
DBNAME="badapple2"
DBSCHEMA="public"
DBUSR="frog"
DBPW="hoppy"
#
DATADIR="$(cd $HOME/../data/Badapple/data/neo4j/; pwd)"
#
psql -h $DBHOST -p $DBPORT -U $DBUSR -w -d $DBNAME \
	-c "COPY (SELECT cid,cansmi FROM compound ORDER BY cid) TO STDOUT WITH (FORMAT CSV,HEADER,DELIMITER E'\t')" \
	>$DATADIR/compound.tsv
printf "compound.tsv: %d\n" $[$(cat $DATADIR/compound.tsv |wc -l) -1]
#
psql -h $DBHOST -p $DBPORT -U $DBUSR -w -d $DBNAME \
	-c "COPY (SELECT id,scafsmi,kekule_scafsmi,in_drug,pscore FROM scaffold ORDER BY id) TO STDOUT WITH (FORMAT CSV,HEADER,DELIMITER E'\t')" \
	>$DATADIR/scaffold.tsv
printf "scaffold.tsv: %d\n" $[$(cat $DATADIR/scaffold.tsv |wc -l) -1]
#
psql -h $DBHOST -p $DBPORT -U $DBUSR -w -d $DBNAME \
	-c "COPY (SELECT scafid,cid FROM scaf2cpd ORDER BY scafid) TO STDOUT WITH (FORMAT CSV,HEADER,DELIMITER E'\t')" \
	>$DATADIR/scaf2cpd.tsv
printf "scaf2cpd.tsv: %d\n" $[$(cat $DATADIR/scaf2cpd.tsv |wc -l) -1]
#
psql -h $DBHOST -p $DBPORT -U $DBUSR -w -d $DBNAME \
	-c "COPY (SELECT parent_id,child_id FROM scaf2scaf ORDER BY parent_id) TO STDOUT WITH (FORMAT CSV,HEADER,DELIMITER E'\t')" \
	>$DATADIR/scaf2scaf.tsv
printf "scaf2scaf.tsv: %d\n" $[$(cat $DATADIR/scaf2scaf.tsv |wc -l) -1]
###
# aid2descriptors
# Encode newlines in protocol field for TSV compatibility.
(psql -h $DBHOST -p $DBPORT -U $DBUSR -w -d $DBNAME <<__EOF__
COPY (SELECT
	aid,
	regexp_replace(description, E'[\\n\\r]+', '\\n', 'g')
	protocol,
	assay_format,
	assay_type,
	detection_method
FROM aid2descriptors) TO STDOUT WITH (FORMAT CSV,HEADER,DELIMITER E'\t')
__EOF__
	) >$DATADIR/aid2descriptors.tsv
printf "aid2descriptors.tsv: %d\n" $[$(cat $DATADIR/aid2descriptors.tsv |wc -l) -1]
#
# aid2target
psql -h $DBHOST -p $DBPORT -U $DBUSR -w -d $DBNAME \
	-c "COPY (SELECT aid,target_id FROM aid2target) TO STDOUT WITH (FORMAT CSV,HEADER,DELIMITER E'\t')" \
	>$DATADIR/aid2target.tsv
printf "aid2target.tsv: %d\n" $[$(cat $DATADIR/aid2target.tsv |wc -l) -1]
#
# drug
psql -h $DBHOST -p $DBPORT -U $DBUSR -w -d $DBNAME \
	-c "COPY (SELECT drug_id,cansmi,inn FROM drug) TO STDOUT WITH (FORMAT CSV,HEADER,DELIMITER E'\t')" \
	>$DATADIR/drug.tsv
printf "drug.tsv: %d\n" $[$(cat $DATADIR/drug.tsv |wc -l) -1]
#
# scaf2activeaid
psql -h $DBHOST -p $DBPORT -U $DBUSR -w -d $DBNAME \
	-c "COPY (SELECT scafid,aid FROM scaf2activeaid) TO STDOUT WITH (FORMAT CSV,HEADER,DELIMITER E'\t')" \
	>$DATADIR/scaf2activeaid.tsv
printf "scaf2activeaid.tsv: %d\n" $[$(cat $DATADIR/scaf2activeaid.tsv |wc -l) -1]
#
# scaf2drug
psql -h $DBHOST -p $DBPORT -U $DBUSR -w -d $DBNAME \
	-c "COPY (SELECT scafid,drug_id FROM scaf2drug) TO STDOUT WITH (FORMAT CSV,HEADER,DELIMITER E'\t')" \
	>$DATADIR/scaf2drug.tsv
printf "scaf2drug.tsv: %d\n" $[$(cat $DATADIR/scaf2drug.tsv |wc -l) -1]
#
# sub2cpd
psql -h $DBHOST -p $DBPORT -U $DBUSR -w -d $DBNAME \
	-c "COPY (SELECT sid,cid FROM sub2cpd) TO STDOUT WITH (FORMAT CSV,HEADER,DELIMITER E'\t')" \
	>$DATADIR/sub2cpd.tsv
printf "sub2cpd.tsv: %d\n" $[$(cat $DATADIR/sub2cpd.tsv |wc -l) -1]
#
# target
psql -h $DBHOST -p $DBPORT -U $DBUSR -w -d $DBNAME \
	-c "COPY (SELECT target_id,type,external_id,external_id_type,name,taxonomy,taxonomy_id,protein_family FROM target) TO STDOUT WITH (FORMAT CSV,HEADER,DELIMITER E'\t')" \
	>$DATADIR/target.tsv
printf "target.tsv: %d\n" $[$(cat $DATADIR/target.tsv |wc -l) -1]
#
