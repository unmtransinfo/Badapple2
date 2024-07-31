# Badapple2
Bioassay data associative promiscuity pattern learning engine V2. 


## Database (DB) Development Setup
1. Install postgresql with the RDKit cartridge (requires sudo):
`apt install postgresql-14-rdkit`
2. Run `bash sh_scripts/db/create_db.sh`
3. Connect to db with `psql -d badapple2`
4. Run `CREATE EXTENSION rdkit;`. This should return `CREATE EXTENSION`.
5. (Optional) You can test the RDKit cartridge with the `mol_to_smiles` command:
```
badapple2=# select mol_to_smiles(mol_from_smiles('O1OCCCC1'));
 mol_to_smiles 
---------------
 C1CCOOC1
(1 row)
```