"""
@author Jack Ringer
Date: 11/20/2024
Description:
File with various utilities related to processing drug targets (proteins, genes, etc)
"""

import re

# see https://www.uniprot.org/help/accession_numbers
UNIPROT_REGEX = r"[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2}"


def strip_version(protein_accession: str):
    # some accession strings include version at the end
    # e.g., "NP_004408.1" indicates version 1 (".1")
    # remove these versions so the accession can be used w/ PubChem API
    pos = protein_accession.rfind(".")
    if pos != -1:
        return protein_accession[:pos]
    return protein_accession


def is_valid_uniprot_id(uniprot_candidate: str):
    return re.match(UNIPROT_REGEX, uniprot_candidate)
