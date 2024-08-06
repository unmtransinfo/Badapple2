-- This script uses the relation "scaftree" in table "scaffold"
-- to fill the "scaf2scaf" table. 
-- Assumes "scaffold" has already been initialized/loaded.
-- Credit to Claude AI for writing this script

-- Insert data into scaf2scaf table
WITH RECURSIVE 
n_scaffolds AS (
    SELECT scaftree, ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) as rn
    FROM scaffold
),
split(parent_id, rest, rn) AS (
    SELECT 
        CASE 
            WHEN position(':' in scaftree) > 0 
            THEN substr(scaftree, 1, position(':' in scaftree) - 1)::INTEGER
            ELSE NULL
        END,
        CASE 
            WHEN position(':' in scaftree) > 0 
            THEN substr(scaftree, position(':' in scaftree) + 2, length(scaftree) - position(':' in scaftree) - 2)
            ELSE NULL 
        END,
        rn
    FROM n_scaffolds
    WHERE position(':' in scaftree) > 0  -- Only process entries with children
    
    UNION ALL
    
    SELECT 
        parent_id,
        CASE 
            WHEN position(',' in rest) > 0 
            THEN substr(rest, position(',' in rest) + 1)
            ELSE NULL
        END,
        rn
    FROM split
    WHERE rest IS NOT NULL
),
extracted_ids AS (
    SELECT 
        parent_id,
        CASE 
            WHEN position(',' in rest) > 0 
            THEN substr(rest, 1, position(',' in rest) - 1)
            ELSE rest
        END AS child_id,
        rn
    FROM split
    WHERE rest IS NOT NULL
)
INSERT INTO scaf2scaf (parent_id, child_id)
SELECT parent_id, child_id::INTEGER
FROM extracted_ids
WHERE child_id ~ '^[0-9]+$';