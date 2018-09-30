import os
import numpy as np
import urllib.request
import re
import pandas as pd


def parse_table(table):
    pattern = re.compile("([A-Z][A-Za-z\.\,\s]+?)\s\.{2,}:"
                         "\s+?([\d\.\,]+?)\s+?"
                         "((?:[A-Za-z]+\s\d+)|(?:\(NA\)))\s+"
                         "((?:[A-Za-z]+\s\d+\s-\s[A-Za-z]+\s\d+)|(?:\(NA\)))\s+"
                         "((?:[A-Za-z]+\s\d+)|(?:\(NA\)))\s+"
                         "((?:[A-Za-z]+\s\d+)|(?:\(NA\)))\s+"
                         "((?:[A-Za-z]+\s\d+\s-\s[A-Za-z]+\s\d+)|(?:\(NA\)))\s+"
                         "((?:[A-Za-z]+\s\d+)|(?:\(NA\)))\s+")
    columns = ["Crop", "Acres",
               "Plant Begin", "Plant Most Active", "Plant End",
               "Harvest Begin", "Harvest Most Active", "Harvest End"]
    data = np.array([row for row in re.findall(pattern, table)])
    return pd.DataFrame(data, columns=columns)


def fetch_data(remote_path):
    pattern = re.compile("Usual Planting and Harvesting Dates by Crop - ([A-Za-z]+?)\r"
                         "(?:[\s\S]+?-{90,}){2}(?:([\s\S]+?)-{90,})")
    req = urllib.request.Request(url=remote_path)
    full_table = None
    with urllib.request.urlopen(req) as f:
        contents = f.read().decode('utf-8')
        matches = re.findall(pattern, contents)
        for match in matches:
            state, table = match
            table = parse_table(table)
            table['State'] = state
            full_table = table if full_table is None else pd.concat([full_table, table])
    full_table.to_csv("plant_harvest")


def main():
    remote_doc = r"http://usda.mannlib.cornell.edu/usda/current/planting/planting-10-29-2010.txt"

    fetch_data(remote_doc)


main()
