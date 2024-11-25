/*
Author: Jack Ringer (+copilot)
Date: 11/25/2024
Description:  
Validates that the number of entries for each scaffold in the "scaf2activeaid"
table matches with the nass_active table. Should return an empty table!

Usage: psql -d badapple2 -f validate_scaf2activeaid.sql
*/
-- validate_scaf2activeaid.sql
COPY (
    SELECT
        s.id AS scafid,
        s.nass_active,
        COUNT(a.scafid) AS count
    FROM
        scaffold s
    LEFT JOIN
        scaf2activeaid a ON s.id = a.scafid
    GROUP BY
        s.id,
        s.nass_active
    HAVING
        s.nass_active != COUNT(a.scafid)
) TO STDOUT WITH (
    FORMAT 'csv',
    DELIMITER ',',
    HEADER TRUE
);