import io
import os
import urllib

import pandas as pd
import numpy as np


class UseData(object):
    def __init__(self, use_dir, usgs_url):
        self.use_dir = use_dir
        self.usgs_url = usgs_url

        # Initialize storage space
        if not os.path.isdir(use_dir):
            os.makedirs(use_dir)

        # Fetch use data from USGS website
        self.pull_use_data()

    def pull_use_data(self):
        """ Pull use data from usgs.gov """
        pairs = [('high', i) for i in range(1, 8)] + [('low', i) for i in range(8, 15)]
        for level, table_num in pairs:
            url = self.usgs_url.format(level, table_num)
            outfile = os.path.join(self.use_dir, "{}_{}.txt".format(level, table_num))
            if not os.path.exists(outfile):
                print("\tPulling use data from {}...".format(url))
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req) as response:
                    table = pd.read_csv(io.StringIO(response.read().decode('utf-8')), sep="\t")
                    table.to_csv(outfile)


def main():
    use_dir = os.path.join("..", "bin", "use_tables")
    usgs_url = r"http://pubs.usgs.gov/ds/752/EPest.{}.county.estimates.table{}.txt"
    overwrite = False

    UseData(use_dir, usgs_url)

main()