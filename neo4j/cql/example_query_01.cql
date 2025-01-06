MATCH (d:Drug)--(s:Scaffold)--(a:Assay)--(t:Target) WHERE d.INN = "nitazoxanide" RETURN * LIMIT 15 ;
-- MATCH (d:Drug)--(s:Scaffold)--(a:Assay)--(t:Target) WHERE d.INN = "encorafenib" RETURN * LIMIT 50 ;
