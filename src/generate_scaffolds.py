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

from utils.file_utils import close_file, get_csv_writer
from utils.logging import get_and_set_logger


class HierSTopLevel(sg.HierS):
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


def is_valid_scaf(can_smiles: str):
    if len(can_smiles) == 0:
        # empty string given
        return False
    elif can_smiles == "c1ccccc1" or can_smiles == "C1=CC=CC=C1":
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
    scaffold_graph,
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
    scaf_writer.writerow(["scaffold_id", "smiles", "hierarchy", "scaf2scaf"])
    mol2scaf_writer.writerow(["mol_id", "mol_name", "scaffold_id"])
    seen_mols = {}
    seen_scafs = {}
    seen_invalid_scafs = {}
    N = scaffold_graph.num_scaffold_nodes
    # for the "id" just use indexing
    scaf_smile_to_id = dict(
        zip([s for s in scaffold_graph.get_scaffold_nodes()], range(0, N))
    )
    cur_id = N
    for mol_node in scaffold_graph.get_molecule_nodes(data=True):
        mol_name = mol_node[0]
        mol_smiles = mol_node[1]["smiles"]
        if mol_smiles in seen_mols:
            # don't bother with duplicates
            continue
        seen_mols[mol_smiles] = True
        mol_scaffolds = scaffold_graph.get_scaffolds_for_molecule(mol_name, data=True)
        mol_id = cur_id
        mol_writer.writerow([mol_id, mol_smiles, mol_name])
        cur_id += 1
        for scaf_node in mol_scaffolds:
            scaf_smile = scaf_node[0]
            scaf_id = scaf_smile_to_id[scaf_smile]
            if scaf_id in seen_invalid_scafs or not (is_valid_scaf(scaf_smile)):
                seen_invalid_scafs[scaf_id] = True
            else:
                mol2scaf_writer.writerow([mol_id, mol_name, scaf_id])
                if scaf_id not in seen_scafs:
                    scaf_hierarchy = scaf_node[1]["hierarchy"]
                    scaf2scaf_str = _get_sub_scaffolds(
                        scaffold_graph, scaf_id, scaf_smile, scaf_smile_to_id
                    )
                    scaf_writer.writerow(
                        [scaf_id, scaf_smile, scaf_hierarchy, scaf2scaf_str]
                    )
                    seen_scafs[scaf_id] = True
    close_file(f_mol)
    close_file(f_scaf)
    close_file(f_mol2scaf)


def main(args):
    network = HierSTopLevel.from_smiles_file(
        file_name=args.i,
        header=args.iheader,
        delimiter=args.idelim,
        smiles_column=args.smiles_column,
        name_column=args.name_column,
        ring_cutoff=args.max_rings,
        progress=True,
    )
    write_outs(network, args.o_mol, args.o_scaf, args.o_mol2scaf, "\t")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffolds compare", epilog="")
    args = parse_args(parser)
    logger = get_and_set_logger(args.log_fname)
    main(args)
