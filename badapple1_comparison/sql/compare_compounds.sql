-- Connect to the first database
\c badapple

-- Enable the dblink extension if not already enabled
CREATE EXTENSION IF NOT EXISTS dblink;

-- Create a temporary table to store the results
CREATE TEMPORARY TABLE comparison_results (
    comparison_type TEXT,
    cid INTEGER,
    isosmi TEXT
);

-- Insert rows that are in badapple but not in badapple_comparison
INSERT INTO comparison_results (comparison_type, cid, isosmi)
SELECT 'Only in badapple', cid, isosmi
FROM compound
EXCEPT
SELECT 'Only in badapple', cid, isosmi
FROM dblink('dbname=badapple_comparison', 'SELECT cid, isosmi FROM compound') AS comp(cid INTEGER, isosmi TEXT);

-- Insert rows that are in badapple_comparison but not in badapple
INSERT INTO comparison_results (comparison_type, cid, isosmi)
SELECT 'Only in badapple_comparison', cid, isosmi
FROM dblink('dbname=badapple_comparison', 'SELECT cid, isosmi FROM compound') AS comp(cid INTEGER, isosmi TEXT)
EXCEPT
SELECT 'Only in badapple_comparison', cid, isosmi
FROM compound;

-- Output the results to a file
\copy (SELECT * FROM comparison_results ORDER BY comparison_type, cid) TO 'compounds_compare.txt' WITH CSV HEADER;

-- Drop the temporary table
DROP TABLE comparison_results;