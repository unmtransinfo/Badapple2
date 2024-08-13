-- NOTE: will only compare CIDs contained in both databases
-- (use compare_compounds.sql to run this comparison)
-- Connect to the first database
\c badapple

-- Enable the dblink extension if not already enabled
CREATE EXTENSION IF NOT EXISTS dblink;

-- Create a temporary table to store the results
CREATE TEMPORARY TABLE comparison_results (
    cid INTEGER,
    nsub_total_badapple INTEGER,
    nsub_total_comparison INTEGER,
    nsub_tested_badapple INTEGER,
    nsub_tested_comparison INTEGER,
    nsub_active_badapple INTEGER,
    nsub_active_comparison INTEGER,
    nass_tested_badapple INTEGER,
    nass_tested_comparison INTEGER,
    nass_active_badapple INTEGER,
    nass_active_comparison INTEGER,
    nsam_tested_badapple INTEGER,
    nsam_tested_comparison INTEGER,
    nsam_active_badapple INTEGER,
    nsam_active_comparison INTEGER
);

-- Insert rows where the specified columns differ between badapple and badapple_comparison
INSERT INTO comparison_results (cid, nsub_total_badapple, nsub_total_comparison, nsub_tested_badapple, nsub_tested_comparison, nsub_active_badapple, nsub_active_comparison, nass_tested_badapple, nass_tested_comparison, nass_active_badapple, nass_active_comparison, nsam_tested_badapple, nsam_tested_comparison, nsam_active_badapple, nsam_active_comparison)
SELECT 
    b.cid,
    b.nsub_total, c.nsub_total,
    b.nsub_tested, c.nsub_tested,
    b.nsub_active, c.nsub_active,
    b.nass_tested, c.nass_tested,
    b.nass_active, c.nass_active,
    b.nsam_tested, c.nsam_tested,
    b.nsam_active, c.nsam_active
FROM 
    compound b
JOIN 
    dblink('dbname=badapple_comparison', 'SELECT cid, nsub_total, nsub_tested, nsub_active, nass_tested, nass_active, nsam_tested, nsam_active FROM compound') AS c(cid INTEGER, nsub_total INTEGER, nsub_tested INTEGER, nsub_active INTEGER, nass_tested INTEGER, nass_active INTEGER, nsam_tested INTEGER, nsam_active INTEGER)
ON 
    b.cid = c.cid
WHERE 
    b.nsub_total <> c.nsub_total OR
    b.nsub_tested <> c.nsub_tested OR
    b.nsub_active <> c.nsub_active OR
    b.nass_tested <> c.nass_tested OR
    b.nass_active <> c.nass_active OR
    b.nsam_tested <> c.nsam_tested OR
    b.nsam_active <> c.nsam_active;

-- Output the results to a file
\copy (SELECT * FROM comparison_results ORDER BY cid) TO 'compounds_compare_stats.csv' WITH CSV HEADER;

-- Drop the temporary table
DROP TABLE comparison_results;