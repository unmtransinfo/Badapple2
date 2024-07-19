DO $$
DECLARE
    N INTEGER := 25;  -- Set your desired limit here
BEGIN
    -- Create and populate the temporary table for the subset of compounds
    CREATE TEMP TABLE temp_compound AS
    WITH first_N_cids AS (
        SELECT DISTINCT cid
        FROM scaf2cpd
        ORDER BY cid
        LIMIT N
    )
    SELECT c.*
    FROM compound c
    JOIN first_N_cids f
    ON c.cid = f.cid;

    -- Create and populate the temporary table for the subset of scaffolds
    CREATE TEMP TABLE temp_scaffold AS
    WITH first_N_cids AS (
        SELECT DISTINCT cid
        FROM scaf2cpd
        ORDER BY cid
        LIMIT N
    ),
    first_N_scafids AS (
        SELECT DISTINCT scafid
        FROM scaf2cpd
        WHERE cid IN (SELECT cid FROM first_N_cids)
    )
    SELECT s.*
    FROM scaffold s
    JOIN first_N_scafids f
    ON s.id = f.scafid;

    -- Create and populate the temporary table for the subset of scaf2cpd
    CREATE TEMP TABLE temp_scaf2cpd AS
    WITH first_N_cids AS (
        SELECT DISTINCT cid
        FROM scaf2cpd
        ORDER BY cid
        LIMIT N
    )
    SELECT s2c.*
    FROM scaf2cpd s2c
    JOIN first_N_cids f
    ON s2c.cid = f.cid;
END $$;
-- export to files
COPY temp_compound TO STDOUT (FORMAT 'csv', DELIMITER E'\t', HEADER) \g compounds_subset.tsv
COPY temp_scaffold TO STDOUT (FORMAT 'csv', DELIMITER E'\t', HEADER) \g scaffolds_subset.tsv
COPY temp_scaf2cpd TO STDOUT (FORMAT 'csv', DELIMITER E'\t', HEADER) \g scaf2cpd_subset.tsv
