/*
Author: Jack Ringer
Date: 12/2/2024
Description:  
SQL script which validates that, for all cases where a given scaffold's
pScore differs between badapple2 and badapple_classic, at least ONE of the scaffold's statistics
also differ.


Usage: psql -d badapple2 -f validate_pscore_differences.sql
*/

CREATE EXTENSION IF NOT EXISTS dblink;

-- Create a temporary table to store the results
CREATE TEMPORARY TABLE comparison_results (
    scafsmi TEXT,
    pscore_2 FLOAT,
    pscore_classic FLOAT,
    nsub_total_2 INTEGER,
    nsub_total_classic INTEGER,
    nsub_tested_2 INTEGER,
    nsub_tested_classic INTEGER,
    nsub_active_2 INTEGER,
    nsub_active_classic INTEGER,
    nass_tested_2 INTEGER,
    nass_tested_classic INTEGER,
    nass_active_2 INTEGER,
    nass_active_classic INTEGER,
    nsam_tested_2 INTEGER,
    nsam_tested_classic INTEGER,
    nsam_active_2 INTEGER,
    nsam_active_classic INTEGER
);

-- Insert rows where the specified columns differ between badapple2 and badapple_classic
INSERT INTO comparison_results (scafsmi, pscore_2, pscore_classic, nsub_total_2, nsub_total_classic, nsub_tested_2, nsub_tested_classic, nsub_active_2, nsub_active_classic, nass_tested_2, nass_tested_classic, nass_active_2, nass_active_classic, nsam_tested_2, nsam_tested_classic, nsam_active_2, nsam_active_classic)
SELECT 
    b.scafsmi,
    b.pscore, c.pscore,
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
    dblink('dbname=badapple_classic', 'SELECT scafsmi, pscore, nsub_total, nsub_tested, nsub_active, nass_tested, nass_active, nsam_tested, nsam_active FROM scaffold') AS c(scafsmi TEXT, pscore FLOAT, nsub_total INTEGER, nsub_tested INTEGER, nsub_active INTEGER, nass_tested INTEGER, nass_active INTEGER, nsam_tested INTEGER, nsam_active INTEGER)
ON 
    b.scafsmi = c.scafsmi
WHERE 
    b.pscore <> c.pscore AND
    b.nsub_total = c.nsub_total AND
    b.nsub_tested = c.nsub_tested AND
    b.nsub_active = c.nsub_active AND
    b.nass_tested = c.nass_tested AND
    b.nass_active = c.nass_active AND
    b.nsam_tested = c.nsam_tested AND
    b.nsam_active = c.nsam_active;

-- Output the results to a file
-- Should be an empty file!
\copy (SELECT * FROM comparison_results ORDER BY scafsmi) TO 'validate_pscore_differences.csv' WITH CSV HEADER;

-- Drop the temporary table
DROP TABLE comparison_results;