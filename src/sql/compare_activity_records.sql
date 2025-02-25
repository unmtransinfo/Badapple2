/*
Author: Jack Ringer
Date: 2/25/2025
Description:  
Script to compare the sets of samples (AID, SID, outcome) between
badapple_classic and badapple2.
Returns the number of samples which were present in badapple_classic but not
badapple2 (118,499).

Usage: psql -d badapple2 -f compare_activity_records.sql
*/

-- Enable the dblink extension if not already enabled
CREATE EXTENSION IF NOT EXISTS dblink;

CREATE TABLE temp_activity AS 
SELECT * FROM dblink('dbname=badapple_classic', 'SELECT aid, sid, outcome FROM activity') 
    AS c(aid INTEGER, sid INTEGER, outcome INTEGER);
CREATE INDEX idx_temp_activity ON temp_activity (aid, sid, outcome);
SELECT COUNT(*)
FROM temp_activity c
LEFT JOIN activity n 
    ON c.aid = n.aid AND c.sid = n.sid AND c.outcome = n.outcome
WHERE n.aid IS NULL;
DROP TABLE temp_activity;