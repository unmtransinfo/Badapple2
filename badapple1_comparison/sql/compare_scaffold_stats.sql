/*
Author: Jack Ringer (+copilot)
Date: 8/15/2024
Description:  
Script to compare the stats (n_cpd_total, ncpd_tested, etc) of the
shared set of scaffolds between badapple and badapple_comparison.
Scaffold SMILES ("scafsmi") are used to identify unique scaffolds for each DB.
Will output a CSV file with all scaffolds that differ in one or more stats.

Usage: psql -d badapple -f compare_scaffold_stats.sql

NOTE: will only compare scaffolds contained in both databases
(based on canonical smiles, use compare_scaffolds.sql to run this comparison)
ASSUMES the "scafsmi" column in both DBs has been canonicalized!
*/

-- Enable the dblink extension if not already enabled
CREATE EXTENSION IF NOT EXISTS dblink;

-- Create a temporary table to store the results
CREATE TEMPORARY TABLE comparison_results (
    scafsmi TEXT,
    ncpd_total_badapple INTEGER,
    ncpd_total_comparison INTEGER,
    ncpd_tested_badapple INTEGER,
    ncpd_tested_comparison INTEGER,
    ncpd_active_badapple INTEGER,
    ncpd_active_comparison INTEGER,
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
INSERT INTO comparison_results (scafsmi, ncpd_total_badapple, ncpd_total_comparison, ncpd_tested_badapple, ncpd_tested_comparison, ncpd_active_badapple, ncpd_active_comparison, nsub_total_badapple, nsub_total_comparison, nsub_tested_badapple, nsub_tested_comparison, nsub_active_badapple, nsub_active_comparison, nass_tested_badapple, nass_tested_comparison, nass_active_badapple, nass_active_comparison, nsam_tested_badapple, nsam_tested_comparison, nsam_active_badapple, nsam_active_comparison)
SELECT 
    b.scafsmi,
    b.ncpd_total, c.ncpd_total,
    b.ncpd_tested, c.ncpd_tested,
    b.ncpd_active, c.ncpd_active,
    b.nsub_total, c.nsub_total,
    b.nsub_tested, c.nsub_tested,
    b.nsub_active, c.nsub_active,
    b.nass_tested, c.nass_tested,
    b.nass_active, c.nass_active,
    b.nsam_tested, c.nsam_tested,
    b.nsam_active, c.nsam_active
FROM 
    scaffold b
JOIN 
    dblink('dbname=badapple_comparison', 'SELECT scafsmi, ncpd_total, ncpd_tested, ncpd_active, nsub_total, nsub_tested, nsub_active, nass_tested, nass_active, nsam_tested, nsam_active FROM scaffold') AS c(scafsmi TEXT, ncpd_total INTEGER, ncpd_tested INTEGER, ncpd_active INTEGER, nsub_total INTEGER, nsub_tested INTEGER, nsub_active INTEGER, nass_tested INTEGER, nass_active INTEGER, nsam_tested INTEGER, nsam_active INTEGER)
ON 
    b.scafsmi = c.scafsmi
WHERE 
    b.ncpd_total <> c.ncpd_total OR
    b.ncpd_tested <> c.ncpd_tested OR
    b.ncpd_active <> c.ncpd_active OR
    b.nsub_total <> c.nsub_total OR
    b.nsub_tested <> c.nsub_tested OR
    b.nsub_active <> c.nsub_active OR
    b.nass_tested <> c.nass_tested OR
    b.nass_active <> c.nass_active OR
    b.nsam_tested <> c.nsam_tested OR
    b.nsam_active <> c.nsam_active;

-- Output the results to a file
\copy (SELECT * FROM comparison_results ORDER BY scafsmi) TO 'scaffold_compare_stats.csv' WITH CSV HEADER;

-- Drop the temporary table
DROP TABLE comparison_results;