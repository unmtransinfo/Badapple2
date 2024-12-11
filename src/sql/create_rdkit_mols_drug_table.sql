SELECT
	drug_id, mol
INTO
	mols_drug
FROM
	(SELECT drug_id, mol_from_smiles(regexp_replace(cansmi,E'\\\\s+.*$','')::cstring) AS mol
	FROM drug) t
WHERE
	mol IS NOT NULL
	;
