/*
Author: Jack Ringer (+copilot)
Date: 8/15/2024
Description:  
Script to compare the sets of compounds (based on CID and isomeric SMILES)
between the badapple and badapple_classic DB. 
Will output a CSV file with all rows that are present in one DB but not the other. 
File will be empty if there are no differences.

Usage: psql -d badapple -f compare_compounds.sql
*/


-- Enable the dblink extension if not already enabled
CREATE EXTENSION IF NOT EXISTS dblink;

-- Create a temporary table to store the results
CREATE TEMPORARY TABLE comparison_results (
    comparison_type TEXT,
    cid INTEGER,
    isosmi TEXT
);

-- Insert rows that are in badapple but not in badapple_classic
INSERT INTO comparison_results (comparison_type, cid, isosmi)
SELECT 'Only in badapple', cid, isosmi
FROM compound
EXCEPT
SELECT 'Only in badapple', cid, isosmi
FROM dblink('dbname=badapple_classic', 'SELECT cid, isosmi FROM compound') AS comp(cid INTEGER, isosmi TEXT);

-- Insert rows that are in badapple_classic but not in badapple
INSERT INTO comparison_results (comparison_type, cid, isosmi)
SELECT 'Only in badapple_classic', cid, isosmi
FROM dblink('dbname=badapple_classic', 'SELECT cid, isosmi FROM compound') AS comp(cid INTEGER, isosmi TEXT)
EXCEPT
SELECT 'Only in badapple_classic', cid, isosmi
FROM compound;

-- Output the results to a file
\copy (SELECT * FROM comparison_results ORDER BY comparison_type, cid) TO 'compounds_compare.csv' WITH CSV HEADER;

-- Drop the temporary table
DROP TABLE comparison_results;