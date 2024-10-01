CREATE TEMPORARY TABLE scafsmi_duplicates AS
    SELECT 
        s.id AS scafid, 
        s.scafsmi,
        c.cid, 
        c.isosmi
    FROM 
        scaffold s
    JOIN 
        scaf2cpd sc2 ON s.id = sc2.scafid
    JOIN 
        compound c ON sc2.cid = c.cid
    WHERE 
        s.scafsmi IN (
            SELECT 
                scafsmi 
            FROM 
                scaffold 
            GROUP BY 
                scafsmi 
            HAVING 
                COUNT(*) > 1
        )
    GROUP BY 
        s.id, s.scafsmi, c.cid, c.isosmi
    ORDER BY 
        s.scafsmi;
\copy (SELECT * FROM scafsmi_duplicates) TO 'duplicate-scafsmis.tsv' WITH CSV DELIMITER E'\t' HEADER;

DROP TABLE scafsmi_duplicates;