"""
@author Jack Ringer
Date: 11/12/2024
Description:
HierS implementation based on ScaffoldGraph with some modifications.
Moving to separate file from generate_scaffolds.py to reduce clutter.
- Credit to ScaffoldGraph: https://github.com/UCLCheminformatics/ScaffoldGraph
- Credit to useful-rdkit-utils: https://github.com/PatWalters/useful_rdkit_utils/tree/master
"""

import loguru
import scaffoldgraph as sg
from rdkit import Chem
from scaffoldgraph.core.fragment import (
    get_annotated_murcko_scaffold,
    get_murcko_scaffold,
)
from scaffoldgraph.core.graph import init_molecule_name
from scaffoldgraph.core.scaffold import Scaffold
from scaffoldgraph.io import *
from scaffoldgraph.utils import suppress_rdlogger
from tqdm import tqdm
from useful_rdkit_utils import RingSystemFinder


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
        # this is an edge case, but fragment SMILES output by ScaffoldGraph do not play nice with other functions in RDKit
        # we keep these fragments so we can derive scaffolds from each frag
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

    def __init__(self, *args, logger=None, identifier_type="canon_smiles", **kwargs):
        super().__init__(*args, **kwargs)
        # Track scaffolds that couldn't be Kekulized
        # (these structures are invalid for RDKit PostgreSQL cartridge)
        self.non_kekule_scaffolds = set()
        self.identifier_type = identifier_type
        self.rsf = RingSystemFinder()
        if logger is None:
            logger = loguru.logger
        self.logger = logger
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
        self.logger.info(f"No top level scaffold for molecule: {name}")
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

    @suppress_rdlogger()
    def _construct(self, molecules, init_args, ring_cutoff=10, progress=False):
        """Private method for graph construction, called by constructors.
        Modified to count ring systems instead of rings when filtering.

        The constructor is fairly generic allowing the user to customise
        hierarchy construction by changing the _hierarchy_constructor
        function. The user also has further control of this process and
        is able to change how a scaffold is initialized (`_initialize_scaffold`),
        how it is preprocessed (`_preprocess_scaffold`) and how molecules with
        no top-level scaffold (i.e. linear molecules) are handled.

        Parameters
        ----------
        molecules : iterable
            An iterable of rdkit molecules for processing
        init_args : dict
            A dictionary containing arguments for scaffold initialization and
            preprocessing.
        ring_cutoff : int, optional
            Ignore molecules with more than the specified number of ring systems to avoid
            extended processing times. The default is 10.
        progress : bool, optional
            If True show a progress bar monitoring progress. The default is False.

        See Also
        --------
        _initialize_scaffold
        _preprocess_scaffold
        _process_no_top_level

        """
        desc, progress = self.__class__.__name__, progress is False
        for molecule in tqdm(
            molecules,
            disable=progress,
            desc=desc,
            miniters=1,
            dynamic_ncols=True,
        ):
            if molecule is None:
                self.logger.info("Molecule was none")
                continue
            init_molecule_name(molecule)
            # CHANGE: count ring systems instead of number of rings
            n_ring_systems = len(self.rsf.find_ring_systems(molecule))
            if n_ring_systems > ring_cutoff:
                name = molecule.GetProp("_Name")
                self.logger.warning(
                    f"Molecule {name} filtered (> {ring_cutoff} ring systems)"
                )
                self.add_molecule_node(
                    molecule
                )  # add molecule to graph so that it will still be in out file
                # END CHANGE
                self.graph["num_filtered"] = self.graph.get("num_filtered", 0) + 1
                continue
            scaffold = self._initialize_scaffold(molecule, init_args)
            if scaffold is not None:
                self._hierarchy_constructor(scaffold)
