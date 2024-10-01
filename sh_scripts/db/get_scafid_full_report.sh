#!/bin/bash

# author Jack Ringer
# Date: 10/1/2024
# Description:
# For a given list of scafids (space-separated), fetch the following information and save it to a TSV file:
# 1) associated CIDs
# 2) (for each CID) associated SIDs
# 3) (for each SID) associated AIDs and outcome
# Example usage:
# bash sh_scripts/db/get_scafid_full_report.sh "badapple_classic" "user" "password" "10312 31202" "scafid_report_test.tsv"


# Check if the correct number of arguments is provided
if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <db_name> <db_user> <db_password> <scafid_list> <output_file>"
    exit 1
fi

# Input arguments
db_name=$1
db_user=$2
db_password=$3
scafid_list=$4
output_file=$5

# Convert the scafid list to a comma-separated string
scafid_str=$(echo $scafid_list | tr ' ' ',')

# SQL commands
sql_commands=$(cat <<EOF
-- Create the temporary table temp_cid_sid
CREATE TEMP TABLE temp_cid_sid AS
SELECT
    scaf2cpd.scafid,
    scaf2cpd.cid,
    sub2cpd.sid
FROM
    scaf2cpd
JOIN
    sub2cpd ON scaf2cpd.cid = sub2cpd.cid
WHERE
    scaf2cpd.scafid IN ($scafid_str);

-- Create the temporary table temp_report
CREATE TEMP TABLE temp_report AS
SELECT
    temp_cid_sid.scafid,
    temp_cid_sid.cid,
    temp_cid_sid.sid,
    activity.aid,
    activity.outcome
FROM
    temp_cid_sid
JOIN
    activity ON temp_cid_sid.sid = activity.sid;

\COPY temp_report TO '$output_file' WITH (FORMAT csv, DELIMITER E'\t', HEADER);
EOF
)

PGPASSWORD=$db_password psql -d $db_name -U $db_user <<EOF
$sql_commands
EOF