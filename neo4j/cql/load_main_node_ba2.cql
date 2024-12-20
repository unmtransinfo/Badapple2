// Loads nodes and edges from TSVs produced by ba_export.sh, copied to
// default import dir /var/lib/neo4j/import/.
////
// See https://neo4j.com/docs/getting-started/current/cypher-intro/load-csv/
// CALL dbms.security.createUser('www', 'foobar')
// In Community Edition, all users have admin privileges.
////


////
// NODES:
//	Compound
//	Scaffold
//	Substance
//	Assay

// Constraints.  Index auto-generated with uniqueness constraint.
DROP CONSTRAINT cid_unique IF EXISTS;
DROP CONSTRAINT scafid_unique IF EXISTS;
CREATE CONSTRAINT cid_unique FOR (n:Compound) REQUIRE n.ID IS UNIQUE ;
CREATE CONSTRAINT scafid_unique FOR (n:Scaffold) REQUIRE n.ID IS UNIQUE ;
// How to show:
// SHOW CONSTRAINTS ;

// Compound:
LOAD CSV WITH HEADERS FROM "file:///badapple/compound.tsv"
AS row FIELDTERMINATOR '\t' WITH row
WHERE row.cid IS NOT NULL AND row.cansmi IS NOT NULL
CREATE (g:Compound { ID:row.cid, SMILES:trim(row.cansmi)}) ;

// Scaffold:
LOAD CSV WITH HEADERS FROM "file:///badapple/scaffold.tsv"
AS row FIELDTERMINATOR '\t' WITH row
WHERE row.id IS NOT NULL AND row.scafsmi IS NOT NULL
CREATE (g:Scaffold { ID:row.id, SMILES:trim(row.scafsmi), inDrug:row.in_drug, pScore:row.pscore}) ;

// Assay:
LOAD CSV WITH HEADERS FROM "file:///badapple/aid2descriptors.tsv"
AS row FIELDTERMINATOR '\t' WITH row
WHERE row.aid IS NOT NULL AND row.assay_type IS NOT NULL
CREATE (g:Assay {
	ID:row.aid,
	AssayFormat:row.assay_format,
	AssayType:row.assay_type,
	DetectionMethod:row.detection_method
	}) ;

// Target:
LOAD CSV WITH HEADERS FROM "file:///badapple/target.tsv"
AS row FIELDTERMINATOR '\t' WITH row
WHERE row.target_id IS NOT NULL AND row.external_id IS NOT NULL
CREATE (g:Target {
	ID:row.target_id,
	Name:trim(row.name),
	Type:row.type,
	ProteinFamily:row.protein_family,
	ExternalID:row.external_id,
	ExternalIDType:row.external_id_type,
	Taxonomy:row.taxonomy,
	TaxonomyID:row.taxonomy_id
	}) ;

// Drug:
LOAD CSV WITH HEADERS FROM "file:///badapple/drug.tsv"
AS row FIELDTERMINATOR '\t' WITH row
WHERE row.drug_id IS NOT NULL AND row.cansmi IS NOT NULL
CREATE (g:Drug { ID:row.drug_id, SMILES:row.cansmi, INN:trim(row.inn)}) ;

// Substance:
// LOAD CSV WITH HEADERS FROM "file:///badapple/kg.tsv"
// AS row FIELDTERMINATOR '\t' WITH row
// WHERE row.node_or_edge = 'node' AND row.class = 'Substance'
// CREATE (g:Substance { ID:row.id, Name:trim(row.name)}) ;

////
// Indexes. AUTO-GENERATED WITH UNIQUENESS CONSTRAINTS.
// Community:
// CREATE INDEX compound_index FOR (n:Compound) ON (n.ID) ;
// CREATE INDEX scaffold_index FOR (n:Scaffold) ON (n.ID) ;
// How to drop:
//DROP INDEX compound_index ;

// Report node counts:
MATCH (c:Compound) RETURN COUNT(c) AS COMPOUND_COUNT ;
MATCH (d:Drug) RETURN COUNT(d) AS DRUG_COUNT ;
MATCH (s:Scaffold) RETURN COUNT(s) AS SCAFFOLD_COUNT ;
MATCH (a:Assay) RETURN COUNT(a) AS ASSAY_COUNT ;
MATCH (t:Target) RETURN COUNT(t) AS TARGET_COUNT ;
