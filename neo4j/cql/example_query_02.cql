MATCH (d:Drug)--(s:Scaffold)--(a:Assay)--(t:Target) WHERE s.SMILES = "c1ccc(-c2cc[nH]n2)cc1" RETURN * LIMIT 15 ;
