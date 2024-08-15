/*
Author: Jack Ringer (+copilot)
Date: 8/15/2024
Description:  
Script to compare the sets of scaffolds (based on canonical SMILES)
between the badapple and badapple_comparison DB. 
Will output a CSV file with all scafs that are present in one DB but not the other. 
File will be empty if there are no differences.

Usage: psql -d badapple -f compare_scaffolds.sql

NOTE: This script assumes both DBs have canonicalized their SMILES using
rdkit. The SMILES in badapple DB were originally not canonicalized in this way.
Hence, uncomment line 22 below (UPDATE scaffold SET ...) to canonicalize these
SMILES if you have not done so already.
*/

-- Enable the dblink extension if not already enabled
CREATE EXTENSION IF NOT EXISTS dblink;
CREATE EXTENSION IF NOT EXISTS rdkit;

-- canonicalize scaffolds in original badapple DB (this was done using openbabel originally, using rdkit now):
-- UPDATE scaffold SET scafsmi = mol_to_smiles(mols_scaf.scafmol) FROM mols_scaf WHERE mols_scaf.id = scaffold.id;

-- Create a temporary table to store the results
CREATE TEMPORARY TABLE comparison_results (
    comparison_type TEXT,
    scafsmi TEXT
);

-- Insert rows that are in badapple but not in badapple_comparison
INSERT INTO comparison_results (comparison_type, scafsmi)
SELECT 'Only in badapple', scafsmi
FROM scaffold
EXCEPT
SELECT 'Only in badapple', scafsmi
FROM dblink('dbname=badapple_comparison', 'SELECT scafsmi FROM scaffold') AS comp(scafsmi TEXT);

-- Insert rows that are in badapple_comparison but not in badapple
INSERT INTO comparison_results (comparison_type, scafsmi)
SELECT 'Only in badapple_comparison', scafsmi
FROM dblink('dbname=badapple_comparison', 'SELECT scafsmi FROM scaffold') AS comp(scafsmi TEXT)
EXCEPT
SELECT 'Only in badapple_comparison', scafsmi
FROM scaffold;

-- Output the results to a file
\copy (SELECT * FROM comparison_results ORDER BY comparison_type, scafsmi) TO 'scaffolds_compare.csv' WITH CSV HEADER;

-- Drop the temporary table
DROP TABLE comparison_results;