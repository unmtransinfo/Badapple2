#!/bin/bash
###
# Export Badapple Pg db to TSVs for Neo4j build.
#
DBHOST="localhost"
DBPORT="5442"
DBNAME="badapple_classic"
DBSCHEMA="public"
DBUSR="johnny"
DBPW="appleseed"
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
#
