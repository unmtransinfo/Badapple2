/*
Author: Jack Ringer
Date: 2/10/2025
Description:  
Script to compare the sets of substances (based on SID) between
badapple2 and badapple_classicDB. 

Usage: psql -d badapple2 -f compare_substances.sql
*/
-- Enable the dblink extension if not already enabled
CREATE EXTENSION IF NOT EXISTS dblink;

-- Create a temporary table to store the results
CREATE TEMPORARY TABLE comparison_results (
    comparison_type TEXT,
    sid INTEGER
);

INSERT INTO comparison_results (comparison_type, sid)
SELECT 'Only in badapple2', sid
FROM activity
EXCEPT
SELECT 'Only in badapple2', sid
FROM dblink('dbname=badapple_classic', 'SELECT distinct(sid) FROM activity') AS comp(sid INTEGER);

INSERT INTO comparison_results (comparison_type, sid)
SELECT 'Only in badapple_classic', sid
FROM dblink('dbname=badapple_classic', 'SELECT distinct(sid) FROM activity') AS comp(sid INTEGER)
EXCEPT
SELECT 'Only in badapple_classic', sid
FROM activity;

-- Output the results to a file
\copy (SELECT * FROM comparison_results ORDER BY comparison_type, sid) TO 'substance_compare.csv' WITH CSV HEADER;

-- Drop the temporary table
DROP TABLE comparison_results;