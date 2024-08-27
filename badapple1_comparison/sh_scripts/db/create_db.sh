# Author: Jack Ringer
# Date: 8/27/2024
# Description:
# Initialize database. Based on: https://github.com/unmtransinfo/Badapple/blob/master/sh/Go_badapple_DbCreate.sh

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
CREATE TABLE IF NOT EXISTS $SCHEMA.scaffold (
	id INTEGER PRIMARY KEY,
	scafsmi VARCHAR(512) NOT NULL,
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
CREATE TABLE IF NOT EXISTS $SCHEMA.scaf2scaf (
	parent_id INTEGER,
	child_id INTEGER
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
	) ;
CREATE TABLE $SCHEMA.sub2cpd (
	sid INTEGER PRIMARY KEY,
	cid INTEGER
	) ;
--
CREATE TABLE $SCHEMA.activity (
	aid INTEGER,
	sid INTEGER,
	outcome INTEGER
	) ;
CREATE TABLE $SCHEMA.scaf2cpd (
	scafid INTEGER,
	cid INTEGER
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
EOF