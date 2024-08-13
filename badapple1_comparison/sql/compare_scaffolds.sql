-- Connect to the first database
\c badapple

-- Enable the dblink extension if not already enabled
CREATE EXTENSION IF NOT EXISTS dblink;
CREATE EXTENSION IF NOT EXISTS rdkit;

-- canonicalize scaffolds in original badapple DB (this was done using openbabel originally, using rdkit now):
UPDATE scaffold SET scafsmi = mol_to_smiles(mols_scaf.scafmol) FROM mols_scaf WHERE mols_scaf.id = scaffold.id;

-- Create a temporary table to store the results
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