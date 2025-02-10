/*
Author: Jack Ringer
Date: 2/10/2025
Description:  
Script to compare the sets of compounds (based on canonical SMILES)
between the badapple2 and badapple_classic DB. 
Will output a CSV file with all compounds that are present in one DB but not the other. 
File will be empty if there are no differences.

Usage: psql -d badapple2 -f compare_compound_structs.sql

NOTE: This script assumes both DBs have canonicalized their SMILES using
rdkit.
*/

-- Enable the dblink extension if not already enabled
CREATE EXTENSION IF NOT EXISTS dblink;
CREATE EXTENSION IF NOT EXISTS rdkit;

-- Create a temporary table to store the results
CREATE TEMPORARY TABLE comparison_results (
    comparison_type TEXT,
    cansmi TEXT
);

INSERT INTO comparison_results (comparison_type, cansmi)
SELECT 'Only in badapple2', cansmi
FROM compound
EXCEPT
SELECT 'Only in badapple2', cansmi
FROM dblink('dbname=badapple_classic', 'SELECT cansmi FROM compound') AS comp(cansmi TEXT);

INSERT INTO comparison_results (comparison_type, cansmi)
SELECT 'Only in badapple_classic', cansmi
FROM dblink('dbname=badapple_classic', 'SELECT cansmi FROM compound') AS comp(cansmi TEXT)
EXCEPT
SELECT 'Only in badapple_classic', cansmi
FROM compound;

-- Output the results to a file
\copy (SELECT * FROM comparison_results ORDER BY comparison_type, cansmi) TO 'compound_structs_compare.csv' WITH CSV HEADER;

-- Drop the temporary table
DROP TABLE comparison_results;