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

from rdkit import Chem

from utils.custom_logging import get_and_set_logger
from utils.file_utils import close_file, get_csv_writer
from utils.hiers import CustomHierS


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
        default=10,
        help="Maximum number of ring systems allowed in input compounds. Compounds with > max_rings will not be processed",
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
        help="(integer) column where molecule names are located (for input SMI file). Names should be unique!",
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
    if args.smiles_column == args.name_column:
        raise ValueError(
            "Given smiles_column and name_column cannot be the same. This is because using SMILES as the name can cause issues when input molecules are self-scaffolds and/or scaffolds of another input molecule."
        )
    args_dict = vars(args)
    logger.info(f"Running generate_scaffolds.py with the following args: {args_dict}")
    network = CustomHierS.from_smiles_file(
        file_name=args.i,
        header=args.iheader,
        delimiter=args.idelim,
        smiles_column=args.smiles_column,
        name_column=args.name_column,
        ring_cutoff=args.max_rings,  # note that this is counting ring systems, not rings
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
    logger.info(f"Total number of molecules in graph: {network.num_molecule_nodes}")
    logger.info(f"Total number of scaffolds in graph: {network.num_scaffold_nodes}")
    logger.info(
        f"Total number of input molecules filtered (> max_rings): {network.graph["num_filtered"]}"
    )
    logger.info(
        f"Total number of linear molecules (molecules with no scaffolds) in input: {network.graph["num_linear"]}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate scaffolds using the HierS algorithm", epilog=""
    )
    args = parse_args(parser)
    logger = get_and_set_logger(args.log_fname)
    main(args)
