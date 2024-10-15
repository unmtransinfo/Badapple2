/*
@author Jack Ringer, Copilot
Date: 10/15/2024
Description:
For a specified scafid, get all of the associated PubChem AssayIDs (AID) in the DB.
For each AID, include the following info:
 - total substances tested
 - total substances active
 - (for the given scaffold) associated substances tested
 - associated substances active
*/

DO $$
DECLARE
    inputScafID INTEGER := 515; 
BEGIN
    -- Get the assays associated with scafid
    CREATE TEMP TABLE temp_aid_list AS
    SELECT DISTINCT aid 
    FROM activity 
    WHERE sid IN (
        SELECT sid 
        FROM sub2cpd 
        WHERE cid IN (
            SELECT cid 
            FROM scaf2cpd 
            WHERE scafid = inputScafID
        )
    ) ORDER BY aid;

    -- Get stats for each AID
    CREATE TEMP TABLE temp_aid_stats (
        aid INTEGER,
        pubchem_url TEXT,
        total_substances_tested INTEGER,
        total_substances_active INTEGER,
        scaf_substances_tested INTEGER,
        scaf_substances_active INTEGER
    );

    INSERT INTO temp_aid_stats (aid, total_substances_tested, total_substances_active, scaf_substances_tested, scaf_substances_active, pubchem_url)
    SELECT 
        aid,
        (SELECT COUNT(*) FROM activity WHERE aid = a.aid AND outcome IN (1, 2, 3, 5)) AS total_substances_tested,
        (SELECT COUNT(*) FROM activity WHERE aid = a.aid AND outcome IN (2, 5)) AS total_substances_active,
        (SELECT COUNT(*) FROM activity WHERE aid = a.aid AND sid IN (
            SELECT sid 
            FROM sub2cpd 
            WHERE cid IN (
                SELECT cid 
                FROM scaf2cpd 
                WHERE scafid = inputScafID
            )
        ) AND outcome IN (1, 2, 3, 5)) AS scaf_substances_tested,
        (SELECT COUNT(*) FROM activity WHERE aid = a.aid AND sid IN (
            SELECT sid 
            FROM sub2cpd 
            WHERE cid IN (
                SELECT cid 
                FROM scaf2cpd 
                WHERE scafid = inputScafID
            )
        ) AND outcome IN (2, 5)) AS scaf_substances_active,
        'https://pubchem.ncbi.nlm.nih.gov/bioassay/' || aid AS pubchem_url
    FROM temp_aid_list a;
END $$;
COPY temp_aid_stats TO STDOUT (FORMAT 'csv', DELIMITER E'\t', HEADER) \g assay_data_scaf515.tsv
