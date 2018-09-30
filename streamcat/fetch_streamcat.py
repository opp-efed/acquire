import os
import pandas as pd
from ftplib import FTP


def assemble_tables(out_dir, overwrite):
    # Make FTP connection.  FTP site for StreamCat is
    # ftp://newftp.epa.gov/EPADataCommons/ORD/NHDPlusLandscapeAttributes/StreamCat/HydroRegions/
    ftp = FTP('newftp.epa.gov')  # connect to host, default port
    ftp.login()  # user anonymous, passwd anonymous@
    ftp.cwd('EPADataCommons/ORD/NHDPlusLandscapeAttributes/StreamCat/HydroRegions')

    # Initialize file storage
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Loop through region and variable and pull files
    file_index = []
    for variable in streamcat_tables:
        for region in nhd_states:
            dataset = "{}_Region{}.zip".format(variable, region)
            out_dataset = os.path.join(out_dir, dataset)
            if overwrite or not os.path.exists(out_dataset):
                print("Pulling dataset {} from EPA site...".format(dataset))
                ftp.retrbinary('RETR {}'.format(dataset), open(out_dataset, 'wb').write)
            file_index.append((variable, region, out_dataset))
    return file_index


def condense_tables(file_index):
    for variable, region, dataset in file_index:
        dataset = pd.read_csv(dataset)
        print(dataset)
        input()


def main():
    # Set output directory and variables of interest
    output_dir = os.path.join("..", "bin", "StreamCat")
    overwrite = True

    file_index = assemble_tables(output_dir, overwrite)
    condense_tables(file_index)


streamcat_tables = ["Runoff",
                    "Pesticides97",
                    "PRISM_1981_2010",
                    "NLCD2006",
                    "Kffact",
                    "ImperviousSurfaces2006",
                    "CanalDensity",
                    "BFI",
                    "AgMidHiSlopes",
                    "Elevation"]

nhd_states = {'01': {"ME", "NH", "VT", "MA", "CT", "RI", "NY"},
              '02': {"VT", "NY", "PA", "NJ", "MD", "DE", "WV", "DC", "VA"},
              '03N': {"VA", "NC", "SC", "GA"},
              '03S': {"FL", "GA"},
              '03W': {"FL", "GA", "TN", "AL", "MS"},
              '04': {"WI", "MN", "MI", "IL", "IN", "OH", "PA", "NY"},
              '05': {"IL", "IN", "OH", "PA", "WV", "VA", "KY", "TN"},
              '06': {"VA", "KY", "TN", "NC", "GA", "AL", "MS"},
              '07': {"MN", "WI", "SD", "IA", "IL", "MO", "IN"},
              '08': {"MO", "KY", "TN", "AR", "MS", "LA"},
              '09': {"ND", "MN", "SD"},
              '10U': {"MT", "ND", "WY", "SD", "MN", "NE", "IA"},
              '10L': {"CO", "WY", "MN", "NE", "IA", "KS", "MO"},
              '11': {"CO", "KS", "MO", "NM", "TX", "OK", "AR", "LA"},
              '12': {"NM", "TX", "LA"},
              '13': {"CO", "NM", "TX"},
              '14': {"WY", "UT", "CO", "AZ", "NM"},
              '15': {"NV", "UT", "AZ", "NM", "CA"},
              '16': {"CA", "OR", "ID", "WY", "NV", "UT"},
              '17': {"WA", "ID", "MT", "OR", "WY", "UT", "NV"},
              '18': {"OR", "NV", "CA"}}

main()
