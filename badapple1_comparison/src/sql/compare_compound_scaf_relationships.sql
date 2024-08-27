/*
Author: Jack Ringer
Date: 8/14/2024
Description:
This script compares the set of scaffolds for each CID in the badapple
and badapple_comparison DB. For CIDs with different sets of scaffolds
(based on the scafsmis), a row with the CID, compound isomeric SMILES (isosmi), and scafsmis (for both DBs) will be output.
Credit to GitHub copilot for helping write this script.

Usage: psql -d badapple -f compare_compound_scaf_relationships.sql

NOTE: This script assumes that the 'scafsmi' column of both DBs has
been canonicalized.
*/

CREATE EXTENSION IF NOT EXISTS dblink;

-- Create a temporary table to store scaffold data for each compound from both databases
CREATE TEMPORARY TABLE temp_scaffold_data (
    cid INTEGER,
    scafid INTEGER,
    scafsmi TEXT,
    isosmi TEXT,
    source TEXT
);

-- Insert scaffold data from badapple database
INSERT INTO temp_scaffold_data (cid, scafid, scafsmi, isosmi, source)
SELECT c.cid, s.id, s.scafsmi, c.isosmi, 'badapple'
FROM compound c
JOIN scaf2cpd s2c ON c.cid = s2c.cid
JOIN scaffold s ON s2c.scafid = s.id;

-- Insert scaffold data from badapple_comparison database
INSERT INTO temp_scaffold_data (cid, scafid, scafsmi, isosmi, source)
SELECT c.cid, s.id, s.scafsmi, c.isosmi, 'badapple_comparison'
FROM dblink('dbname=badapple_comparison', 'SELECT cid, scafid FROM scaf2cpd') AS s2c(cid INTEGER, scafid INTEGER)
JOIN dblink('dbname=badapple_comparison', 'SELECT id, scafsmi FROM scaffold') AS s(id INTEGER, scafsmi TEXT) ON s2c.scafid = s.id
JOIN dblink('dbname=badapple_comparison', 'SELECT cid, isosmi FROM compound') AS c(cid INTEGER, isosmi TEXT) ON s2c.cid = c.cid;

-- Create a temporary table to store the differences
CREATE TEMPORARY TABLE scaffold_differences AS
SELECT cid, isosmi,
    array_to_string(array_agg(CASE WHEN source = 'badapple' THEN scafsmi END ORDER BY scafsmi), ',') AS badapple_scafsmis,
    array_to_string(array_agg(CASE WHEN source = 'badapple_comparison' THEN scafsmi END ORDER BY scafsmi), ',') AS badapple_comparison_scafsmis,
    array_to_string(array_agg(CASE WHEN source = 'badapple' THEN scafid END ORDER BY scafsmi), ',') AS badapple_ids,
    array_to_string(array_agg(CASE WHEN source = 'badapple_comparison' THEN scafid END ORDER BY scafsmi), ',') AS badapple_comparison_ids
FROM temp_scaffold_data
GROUP BY cid, isosmi
HAVING array_to_string(array_agg(CASE WHEN source = 'badapple' THEN scafsmi END ORDER BY scafsmi), ',') IS DISTINCT FROM array_to_string(array_agg(CASE WHEN source = 'badapple_comparison' THEN scafsmi END ORDER BY scafsmi), ',');

-- Output the differences to a TSV file
\copy (SELECT cid, isosmi, badapple_scafsmis, badapple_comparison_scafsmis, badapple_ids, badapple_comparison_ids FROM scaffold_differences ORDER BY cid) TO 'compound-scaffold_differences.tsv' WITH CSV DELIMITER E'\t' HEADER;

-- Drop the temporary tables
DROP TABLE temp_scaffold_data;
DROP TABLE scaffold_differences;