"""
@author Jack Ringer
Date: 7/1/2024
Description:
Script to download assay data from PubChem using the PUG REST API:
https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest-tutorial#section=Access-to-PubChem-BioAssays 
"""

import io

import pandas as pd
import requests

if __name__ == "__main__":
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/assay/aid/1000/concise/CSV"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.content.decode("utf-8")
        df = pd.read_csv(io.StringIO(data))
        print(df.head())
    else:
        print("Failed to retrieve data. Status code:", response.status_code)
