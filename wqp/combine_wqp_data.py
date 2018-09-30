import pandas as pd


def main():
    # Specify run paths and parameters
    site_file = "station.csv"
    data_file = "narrowresult.csv"
    out_file = "comb_results.csv"
    keep_all_fields = False  # Keep all site file fields if True, confine to location id, and lat/long if False

    # Read csv files
    site_df = pd.read_csv(site_file, keep_default_na=False, na_values=[""])
    if not keep_all_fields:
        site_df = site_df["MonitoringLocationIdentifier", "LatitudeMeasure", "LongitudeMeasure"]
    conc_df = pd.read_csv(data_file, keep_default_na=False, na_values=[""])
    conc_df = conc_df.merge(site_df, on='MonitoringLocationIdentifier')

    # Write to file
    conc_df.to_csv(out_file)


main()
