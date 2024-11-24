# Author: Jack Ringer
# Date: 11/21/2024
# Description:
# Initialize Badapple2 database
# NOTE: If using this script to DB with new data you may want to
# double-check the VARCHAR limits (in parens). Be careful
# with the assay description and protocol (type TEXT means no size limit!)

if [ $# -lt 4 ]; then
	printf "Syntax: %s DB_NAME DB_HOST SCHEMA COMMENT\n" $0
	exit
fi

DB_NAME=$1
DB_HOST=$2
SCHEMA=$3
COMMENT=$4


if [ ! `psql -P pager=off -Al | grep '|' | sed -e 's/|.*$//' | grep "^${DB_NAME}$"` ]; then
	createdb -h $DB_HOST $DB_NAME 
fi

psql -h $DB_HOST -d $DB_NAME -c "COMMENT ON DATABASE ${DB_NAME} IS '$COMMENT'"
psql -h $DB_HOST -d $DB_NAME <<EOF
CREATE TABLE $SCHEMA.scaffold (
	id INTEGER PRIMARY KEY,
	scafsmi VARCHAR(512) NOT NULL UNIQUE,
	kekule_scafsmi VARCHAR(512) NOT NULL UNIQUE,
	scaftree VARCHAR(2048),
	ncpd_total INTEGER,
	ncpd_tested INTEGER,
	ncpd_active INTEGER,
	nsub_total INTEGER,
	nsub_tested INTEGER,
	nsub_active INTEGER,
	nass_tested INTEGER,
	nass_active INTEGER,
	nsam_tested INTEGER,
	nsam_active INTEGER,
	in_drug BOOLEAN,
	pscore FLOAT
	) ;
CREATE TABLE $SCHEMA.scaf2scaf (
	parent_id INTEGER NOT NULL,
	child_id INTEGER NOT NULL
	);
--
CREATE TABLE $SCHEMA.compound (
	cid INTEGER PRIMARY KEY,
	cansmi VARCHAR(2048) NOT NULL,
	isosmi VARCHAR(2048) NOT NULL,
	nsub_total INTEGER,
	nsub_tested INTEGER,
	nsub_active INTEGER,
	nass_tested INTEGER,
	nass_active INTEGER,
	nsam_tested INTEGER,
	nsam_active INTEGER
	);
CREATE TABLE $SCHEMA.sub2cpd (
	sid INTEGER PRIMARY KEY,
	cid INTEGER NOT NULL
	) ;
--
CREATE TABLE $SCHEMA.activity (
	aid INTEGER NOT NULL,
	sid INTEGER NOT NULL,
	outcome INTEGER NOT NULL
	) ;
CREATE TABLE $SCHEMA.scaf2cpd (
	scafid INTEGER NOT NULL,
	cid INTEGER NOT NULL
	);
CREATE TABLE $SCHEMA.metadata (
	db_description VARCHAR(2048),
	db_date_built TIMESTAMP WITH TIME ZONE,
	median_ncpd_tested INTEGER,
	median_nsub_tested INTEGER,
	median_nass_tested INTEGER,
	median_nsam_tested INTEGER,
	nass_total INTEGER
	);
-- start of Badapple2 tables:
CREATE TABLE $SCHEMA.aid2descriptors (
	aid INTEGER PRIMARY KEY,
	description TEXT NOT NULL,
	protocol TEXT NOT NULL,
	assay_format VARCHAR(128),
	assay_type VARCHAR(128),
	detection_method VARCHAR(128)
	);
CREATE TABLE $SCHEMA.aid2target (
	aid INTEGER NOT NULL,
	target_id INTEGER NOT NULL
	);
CREATE TABLE $SCHEMA.drug (
	drug_id INTEGER PRIMARY KEY,
	cansmi VARCHAR(2048) NOT NULL,
	inn VARCHAR(128) NOT NULL
	);
CREATE TABLE $SCHEMA.scaf2activeaid (
	scafid INTEGER NOT NULL,
	aid INTEGER NOT NULL
	);
CREATE TABLE $SCHEMA.scaf2drug (
	scafid INTEGER NOT NULL,
	drug_id INTEGER NOT NULL
	);
CREATE TABLE $SCHEMA.target (
	target_id INTEGER PRIMARY KEY,
	type VARCHAR(64) NOT NULL,
	external_id VARCHAR(64) NOT NULL,
	external_id_type VARCHAR(64) NOT NULL,
	name VARCHAR(256),
	taxonomy VARCHAR(128),
	taxonomy_id INTEGER,
	protein_family VARCHAR(64)
	);
EOF