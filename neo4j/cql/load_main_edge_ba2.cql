////
// EDGES ("relationships")
////
// NOTE: LOAD TSV vals read as strings.
// NOTE: Cypher regex matches ENTIRE string.
////
//Debugging:
//LOAD CSV WITH HEADERS FROM "file:///badapple/kg.tsv"
//AS row FIELDTERMINATOR '\t' WITH row
//MATCH (s {ID:row.sourceId}), (t {ID:row.targetId})
//WHERE row.node_or_edge = 'edge'
//RETURN row.sourceId, row.targetId, s.ID, t.ID ;
////
//Scaffold-Scaffold (SCAF_IN_SCAF)
LOAD CSV WITH HEADERS FROM "file:///badapple/scaf2scaf.tsv"
AS row FIELDTERMINATOR '\t' WITH row
MATCH (p:Scaffold {ID:row.parent_id}), (c:Scaffold {ID:row.child_id})
WHERE row.parent_id IS NOT NULL AND row.child_id IS NOT NULL
CREATE (c)-[:SCAF_IN_SCAF]->(p) ;

//Scaffold-Compound (SCAF_IN_CPD)
LOAD CSV WITH HEADERS FROM "file:///badapple/scaf2cpd.tsv"
AS row FIELDTERMINATOR '\t' WITH row
MATCH (s:Scaffold {ID:row.scafid}), (c:Compound {ID:row.cid})
WHERE row.scafid IS NOT NULL AND row.cid IS NOT NULL
CREATE (s)-[:SCAF_IN_CPD]->(c) ;

//Scaffold-Drug (SCAF_IN_DRUG)
LOAD CSV WITH HEADERS FROM "file:///badapple/scaf2drug.tsv"
AS row FIELDTERMINATOR '\t' WITH row
MATCH (s:Scaffold {ID:row.scafid}), (d:Drug {ID:row.drug_id})
WHERE row.scafid IS NOT NULL AND row.drug_id IS NOT NULL
CREATE (s)-[:SCAF_IN_DRUG]->(d) ;

//Scaffold-Assay (SCAF_ACT_ASSAY)
LOAD CSV WITH HEADERS FROM "file:///badapple/scaf2activeaid.tsv"
AS row FIELDTERMINATOR '\t' WITH row
MATCH (s:Scaffold {ID:row.scafid}), (a:Assay {ID:row.aid})
WHERE row.scafid IS NOT NULL AND row.aid IS NOT NULL
CREATE (s)-[:SCAF_ACT_ASSAY]->(a) ;

//Assay-Target (ASSAY_TARGET)
LOAD CSV WITH HEADERS FROM "file:///badapple/aid2target.tsv"
AS row FIELDTERMINATOR '\t' WITH row
MATCH (t:Target {ID:row.target_id}), (a:Assay {ID:row.aid})
WHERE row.target_id IS NOT NULL AND row.aid IS NOT NULL
CREATE (a)-[:ASSAY_TARGET]->(t) ;

// Report relationship count:
MATCH ()-[r]-() RETURN COUNT(r) AS RELATIONSHIPS_All ;
MATCH ()-[r:SCAF_IN_SCAF]-() RETURN COUNT(r) AS RELATIONSHIPS_SCAF_IN_SCAF ;
MATCH ()-[r:SCAF_IN_CPD]-() RETURN COUNT(r) AS RELATIONSHIPS_SCAF_IN_CPD ;
MATCH ()-[r:SCAF_IN_DRUG]-() RETURN COUNT(r) AS RELATIONSHIPS_SCAF_IN_DRUG ;
MATCH ()-[r:SCAF_ACT_ASSAY]-() RETURN COUNT(r) AS RELATIONSHIPS_SCAF_ACT_ASSAY ;
MATCH ()-[r:ASSAY_TARGET]-() RETURN COUNT(r) AS RELATIONSHIPS_ASSAY_TARGET ;
////
//Delete duplicates:
//MATCH (s)-[r:SCAF_IN_SCAF]->(e) WITH s, e, type(r) AS t, tail(collect(r)) AS c foreach(x IN c | DELETE x)
