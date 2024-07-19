from rdkit import Chem
from rdkit.Chem import rdChemReactions


def print_smis(smiles_list: list[str]):
    for smi in smiles_list:
        print(smi)


if __name__ == "__main__":
    mol_smi = "c1ccc(CCn2cncn2)cc1"
    mol = Chem.MolFromSmiles(mol_smi)
    fragmentation_reaction = rdChemReactions.ReactionFromSmarts(
        "[!#0;R:1]-!@[!#0:2]>>[*:1]-[#0].[#0]-[*:2]"
    )
    products = fragmentation_reaction.RunReactant(mol, 0)
    print(len(products))
    mol_ringsystems = [p[0] for p in products]
    mol_chains_and_linkers = [p[1] for p in products]
    ringsystem_smiles = [Chem.MolToSmiles(m) for m in mol_ringsystems]
    chains_and_linkers_smiles = [Chem.MolToSmiles(m) for m in mol_chains_and_linkers]
    print("mol SMILES:")
    print_smis([mol_smi])
    print("ring systems:")
    print_smis(ringsystem_smiles)
    print("chains and linkers:")
    print_smis(chains_and_linkers_smiles)
