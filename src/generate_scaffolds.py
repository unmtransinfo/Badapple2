"""
@author Jack Ringer
Date: 6/17/2024
Description:
Code for generating scaffolds using the HierS algorithm from 
ScaffoldGraph: https://github.com/UCLCheminformatics/ScaffoldGraph

Outputs are intentionally made to mirror the tables in the original
badapple database.
"""

import argparse

import scaffoldgraph as sg
from loguru import logger
from rdkit import Chem
from scaffoldgraph.core.fragment import (
    get_annotated_murcko_scaffold,
    get_murcko_scaffold,
)
from scaffoldgraph.core.scaffold import Scaffold
from scaffoldgraph.io import *

from utils.custom_logging import get_and_set_logger
from utils.file_utils import close_file, get_csv_writer


def canon_smiles(mol: Chem.Mol, kekule=False):
    # beware of oscillating SMILES when using kekule=True !
    # example:
    # O=C1C=CN2CCCC3=CC=CC1=C32 => O=C1C=CN2CCCC3=C2C1=CC=C3 => O=C1C=CN2CCCC3=CC=CC1=C32
    try:
        canon_smiles = Chem.MolToSmiles(mol, canonical=True, kekuleSmiles=kekule)
        # converting again... why:
        # in edge cases there is some information loss when converting to SMILES
        # by converting twice, we ensure consistency with the PostgreSQL DB and RDKit
        # example of what happens without converting twice:
        # >>> scaf1 = Chem.MolFromSmiles("C1=NC(c2ccccc2)=NP=N1")
        # >>> scaf2 = Chem.MolFromSmiles("c1ccc(-c2ncnpn2)cc1")
        # >>> Chem.MolToSmiles(scaf1) == Chem.MolToSmiles(scaf2)
        # True
        # basically in ScaffoldGraph scaf1 and scaf2 were considered to be different and output different canonSMILES,
        # even though when we reconstruct the scaffolds with these SMILES they are the same
        # this issue happens even with kekule=True, for example:
        # >>> scaf1 = Chem.MolFromSmiles("C(=NC1=C(N2CCCCC2)C=CC=C1)C1=CNN=C1")
        # >>> scaf2 = Chem.MolFromSmiles("C(=NC1=CC=CC=C1N1CCCCC1)C1=CNN=C1")
        # >>> Chem.MolToInchi(scaf1) == Chem.MolToInchi(scaf2)
        # [15:23:11] WARNING: Omitted undefined stereo
        # [15:23:11] WARNING: Omitted undefined stereo
        # True
        # >>> Chem.MolToSmiles(scaf1,kekuleSmiles=True) == Chem.MolToSmiles(scaf2,kekuleSmiles=True)
        # True
        canon_smiles = Chem.MolToSmiles(
            Chem.MolFromSmiles(canon_smiles), canonical=True, kekuleSmiles=kekule
        )
        return canon_smiles
    except:
        # this is an extreme edge case, but certain SMILES output by ScaffoldGraph do not play nice with other functions in RDKit
        # (e.g., Chem.MolFromSmiles)
        # only example seen so far: [c-]1cccc1.c1cc(N2CCCC2)[c-]2[cH-][cH-][cH-][c-]2n1
        # (this was from CID 16717706)
        original_smiles = Chem.MolToSmiles(mol)
        return original_smiles


class CustomHierS(sg.HierS):
    """
    This is a slightly modified version of the original HierS algorithm from ScaffoldGraph. it uses the following changes:
    1) Includes molecules with no top-level scaffold in the graph.
    2) Supports multiple identifier types, rather than only canonical aromatic SMILES
    """

    def __init__(self, *args, identifier_type="canon_smiles", **kwargs):
        super().__init__(*args, **kwargs)
        # Track scaffolds that couldn't be Kekulized
        # (these structures are invalid for RDKit PostgreSQL cartridge)
        self.non_kekule_scaffolds = set()
        self.identifier_type = identifier_type
        if identifier_type == "canon_smiles":
            self.hash_func = canon_smiles
        elif identifier_type == "kekule_smiles":
            self.hash_func = lambda mol: canon_smiles(mol, kekule=True)
        elif identifier_type == "inchi":
            self.hash_func = Chem.MolToInchi
        else:
            raise ValueError(f"Unrecognized identifier_type: {identifier_type}")

    def _process_no_top_level(self, molecule):
        """Private: Process molecules with no top-level scaffold.
        Modified from original code so that molecules with no top-level
        scaffold are still included in the graph.
        Parameters
        ----------
        molecule : rdkit.Chem.rdchem.Mol
            An rdkit molecule determined to have no top-level scaffold.
        """
        name = molecule.GetProp("_Name")
        logger.info(f"No top level scaffold for molecule: {name}")
        self.graph["num_linear"] = self.graph.get("num_linear", 0) + 1
        self.add_molecule_node(
            molecule,
        )
        return None

    def _initialize_scaffold(self, molecule, init_args):
        """Initialize the top-level scaffold for a molecule.
        Modified from the original code to Kekulize the scaffold.

        Initialization generates a murcko scaffold, performs
        any preprocessing required and then adds the scaffold
        node to the graph connecting it to its child molecule.
        This process can be customised in subclasses to modify
        how a scaffold is initialized.

        Parameters
        ----------
        molecule : rdkit.Chem.rdchem.Mol
            A molecule from whicg to initialize a scaffold.
        init_args : dict
            A dictionary containing arguments for scaffold
            initialization and preprocessing.

        Returns
        -------
        scaffold : Scaffold
            A Scaffold object containing the initialized
            scaffold to be processed further (hierarchy
            generation).

        """
        scaffold_rdmol = get_murcko_scaffold(molecule)
        if scaffold_rdmol.GetNumAtoms() <= 0:
            return self._process_no_top_level(molecule)
        scaffold_rdmol = self._preprocess_scaffold(scaffold_rdmol, init_args)
        scaffold = Scaffold(scaffold_rdmol)
        # CHANGE: override default hash_func
        scaffold.hash_func = self.hash_func
        # END CHANGE
        annotation = None
        if init_args.get("annotate") is True:
            annotation = get_annotated_murcko_scaffold(molecule, scaffold_rdmol, False)
        self.add_scaffold_node(scaffold)
        self.add_molecule_node(molecule)
        self.add_molecule_edge(molecule, scaffold, annotation=annotation)
        return scaffold

    def _hierarchy_constructor(self, child):
        parents = (p for p in self.fragmenter.fragment(child) if p)
        for parent in parents:
            # CHANGE: use consistent hash_func as in _initialize_scaffold
            parent.hash_func = self.hash_func
            # END CHANGE
            if parent in self.nodes:
                self.add_scaffold_edge(parent, child)
            else:
                self.add_scaffold_node(parent)
                self.add_scaffold_edge(parent, child)
                if parent.ring_systems.count > 1:
                    self._hierarchy_constructor(parent)


def parse_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--i",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="input compounds (SMI/TSV file)",
    )
    parser.add_argument(
        "--o_scaf",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="output file with detected scaffolds and their ids",
    )
    parser.add_argument(
        "--o_mol",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="output file with input molecules and their ids",
    )
    parser.add_argument(
        "--o_mol2scaf",
        type=str,
        required=True,
        default=argparse.SUPPRESS,
        help="output file mapping molecule ids to associated scaffold ids",
    )
    parser.add_argument(
        "--idelim",
        type=str,
        default="\t",
        help="delim for input SMI/TSV file (default is tab)",
    )
    parser.add_argument(
        "--iheader",
        action="store_true",
        help="input SMILES/TSV has header line",
    )
    parser.add_argument(
        "--max_rings",
        type=int,
        required=False,
        default=20,
        help="Maximum number of rings allowed in input compounds. Compounds with > max_rings will not be processed",
    )
    parser.add_argument(
        "--identifier_type",
        choices=["canon_smiles", "kekule_smiles", "inchi"],
        default="canon_smiles",
        required=False,
        help="Identifier to use when constructing the graph - determines identity of scaffolds (whether or not two scaffolds are the same)",
    )
    parser.add_argument(
        "--include_kekule_smiles",
        type=argparse.BooleanOptionalAction,
        default=True,
        required=False,
        help="Verify scaffold structures can be kekulized and include Kekule SMILES in scaffold output file (can be useful for portability across software platforms)",
    )
    parser.add_argument(
        "--smiles_column",
        type=int,
        default=0,
        help="(integer) column where SMILES are located (for input SMI file)",
    )
    parser.add_argument(
        "--name_column",
        type=int,
        default=1,
        help="(integer) column where molecule names are located (for input SMI file)",
    )
    parser.add_argument(
        "--log_fname",
        help="File to save logs to. If not given will log to stdout.",
        default=None,
    )
    return parser.parse_args()


def is_valid_scaf(scaf_rep: str):
    if len(scaf_rep) == 0:
        # empty string given
        return False
    elif (
        scaf_rep == "c1ccccc1"
        or scaf_rep == "C1=CC=CC=C1"
        or scaf_rep == "InChI=1S/C6H6/c1-2-4-6-5-3-1/h1-6H"
    ):
        # benzene excluded from scaffolds
        return False
    return True


def _get_sub_scaffolds(scaffold_graph, scaf_id: int, scaf_smile: str, scaf_smile_to_id):
    # note: parent scaffolds are sub scaffolds of scaf
    sub_scafs = scaffold_graph.get_parent_scaffolds(scaf_smile)
    sub_scafs = list(filter(is_valid_scaf, sub_scafs))
    scaf2scaf_str = str(scaf_id)
    if len(sub_scafs) > 0:
        scaf2scaf_str += ":("
        for i, sub_scaf_smile in enumerate(sub_scafs):
            sub_scaf_id = scaf_smile_to_id[sub_scaf_smile]
            scaf2scaf_str += str(sub_scaf_id)
            if i < (len(sub_scafs) - 1):
                scaf2scaf_str += ","
        scaf2scaf_str += ")"
    return scaf2scaf_str


def write_outs(
    scaffold_graph: CustomHierS,
    include_kekule_smiles: bool,
    o_mol: str,
    o_scaf: str,
    o_mol2scaf: str,
    odelimeter: str,
) -> None:
    # idx == ids
    mol_writer, f_mol = get_csv_writer(o_mol, odelimeter)
    scaf_writer, f_scaf = get_csv_writer(o_scaf, odelimeter)
    mol2scaf_writer, f_mol2scaf = get_csv_writer(o_mol2scaf, odelimeter)

    # mol_name is from name of mol in input file (e.g., "CID")
    mol_writer.writerow(["mol_id", "smiles", "mol_name"])

    identifier_type = scaffold_graph.identifier_type
    scaf_header = [
        "scaffold_id",
        identifier_type,
        "hierarchy",
        "scaf2scaf",
    ]
    check_kekule = include_kekule_smiles
    include_kekule_smiles = (include_kekule_smiles) and (
        identifier_type != "kekule_smiles"
    )  # no point in having two identical columns
    if include_kekule_smiles:
        scaf_header.insert(2, "kekule_smiles")
    scaf_writer.writerow(scaf_header)

    mol2scaf_writer.writerow(["mol_id", "mol_name", "scaffold_id"])

    seen_scafs = {}
    seen_invalid_scafs = {}
    N = scaffold_graph.num_scaffold_nodes
    # for the "id" just use indexing
    scaf_rep_to_id = dict(
        zip([s for s in scaffold_graph.get_scaffold_nodes()], range(0, N))
    )
    cur_id = N
    for mol_node in scaffold_graph.get_molecule_nodes(data=True):
        mol_name = mol_node[0]
        mol_smiles = mol_node[1]["smiles"]
        mol_scaffolds = scaffold_graph.get_scaffolds_for_molecule(mol_name, data=True)
        mol_id = cur_id
        mol_writer.writerow([mol_id, mol_smiles, mol_name])
        cur_id += 1
        for scaf_node in mol_scaffolds:
            scaf_rep = scaf_node[0]  # can be either inchi or smiles
            scaf_id = scaf_rep_to_id[scaf_rep]
            kekule_smiles = ""
            if check_kekule:
                # track un-kekulizable scaffolds
                try:
                    if identifier_type == "inchi":
                        mol = Chem.MolFromInchi(scaf_rep)
                    else:
                        mol = Chem.MolFromSmiles(scaf_rep)
                    kekule_smiles = Chem.MolToSmiles(
                        mol, canonical=True, kekuleSmiles=True
                    )
                except:
                    logger.info(
                        f"Unable to generate Kekule SMILES for scaffold {scaf_rep} - excluding from output file"
                    )
                    seen_invalid_scafs[scaf_id] = True
            if scaf_id in seen_invalid_scafs or not (is_valid_scaf(scaf_rep)):
                seen_invalid_scafs[scaf_id] = True
            else:
                mol2scaf_writer.writerow([mol_id, mol_name, scaf_id])
                if scaf_id not in seen_scafs:
                    scaf_hierarchy = scaf_node[1]["hierarchy"]
                    scaf2scaf_str = _get_sub_scaffolds(
                        scaffold_graph, scaf_id, scaf_rep, scaf_rep_to_id
                    )
                    scaf_row = [
                        scaf_id,
                        scaf_rep,
                        scaf_hierarchy,
                        scaf2scaf_str,
                    ]
                    if include_kekule_smiles:
                        scaf_row.insert(2, kekule_smiles)
                    scaf_writer.writerow(scaf_row)
                    seen_scafs[scaf_id] = True
    close_file(f_mol)
    close_file(f_scaf)
    close_file(f_mol2scaf)


def main(args):
    network = CustomHierS.from_smiles_file(
        file_name=args.i,
        header=args.iheader,
        delimiter=args.idelim,
        smiles_column=args.smiles_column,
        name_column=args.name_column,
        ring_cutoff=args.max_rings,
        progress=True,
    )
    write_outs(
        network,
        args.include_kekule_smiles,
        args.o_mol,
        args.o_scaf,
        args.o_mol2scaf,
        "\t",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffolds compare", epilog="")
    args = parse_args(parser)
    logger = get_and_set_logger(args.log_fname)
    main(args)
