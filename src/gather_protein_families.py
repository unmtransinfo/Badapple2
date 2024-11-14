"""
@author Jack Ringer
Date: 11/14/2024
Description:
Script to gather protein family information from external sources.
"""

from typing import Tuple

import requests


def _get_family_pharos(uniprot_id: str):
    # get the protein family from pharos using GraphQL api
    api_url = "https://pharos-api.ncats.io/graphql"
    query_str = f"""
        query targetDetails {{
        target(q: {{uniprot: "{uniprot_id}"}}) {{
            fam
        }}
        }}
        """
    response = requests.post(api_url, json={"query": query_str})
    family = None
    if response.status_code == 200:
        data = response.json()
        if data["data"]["target"] is not None:
            family = data["data"]["target"]["fam"]
            return family
    return None


def get_protein_family(uniprot_id: str) -> Tuple[str, str]:
    family = _get_family_pharos(uniprot_id)
    datasource = None
    if family is None:
        pass
    else:
        datasource = "Pharos"
    return family, datasource
