import os

from bs4 import BeautifulSoup
import requests
import pandas as pd
import datetime

import copy


# Pull structure from http://chrisalbon.com/python/beautiful_soup_scrape_table.html
# and https://johnricco.github.io/2017/04/04/python-html/

#TODO add an output that merges all table to be used in following steps

url = "http://www.nmfs.noaa.gov/pr/species/esa/candidate.htm#proposed"

outlocation = r'C:\Users\JConno02\OneDrive - Environmental Protection Agency (EPA)\Documents_C_drive\Projects\ESA' \
              r'\MasterLists\Creation\test'

# Can and Proposed foreign species per NMFS
removed_perNMFS = ['Cephalorhynchus hectori maui', 'Cephalorhynchus hectori hectori', 'Sousa chinensis taiwanensis',
                   'Mustelus schmitti', 'Squatina guggenheim', 'Amblyraja radiata', 'Rhinobatos horkelii',
                   'Squatina argentina', 'Isogomphodon oxyrhynchus', 'Mustelus fasciatus']


def tables_read(tables_html, n):
    n_cols = 0
    n_rows = 0

    # Parse each table

    for row in tables_html[n].find_all("tr"):
        col_tags = row.find_all(["td", "th"])
        if len(col_tags) > 0:
            n_rows += 1
            if len(col_tags) > n_cols:
                n_cols = len(col_tags)

        # Create dataframe
    df = pd.DataFrame(index=range(0, n_rows), columns=range(0, n_cols))

    # Create list to store rowspan values
    skip_index = [0 for i in range(0, n_cols)]

    # Start by iterating over each row in this table...
    row_counter = 0
    for row in tables_html[n].find_all("tr"):

        # Skip row if it's blank
        if len(row.find_all(["td", "th"])) == 0:
            next

        else:

            # Get all cells containing data in this row
            columns = row.find_all(["td", "th"])
            col_dim = []
            row_dim = []
            col_dim_counter = -1
            row_dim_counter = -1
            col_counter = -1
            this_skip_index = copy.deepcopy(skip_index)
            # ROWSPAN AND COLSPAN CHECKS FOR MERGED CELL WHICH ARE TYPICALLY NOT CONSISTENCE ON WEBSITE SEE REFERNCE
            # WEBSITE FOR MORE DETAILS
            for col in columns:

                # Determine cell dimensions
                colspan = col.get("colspan")
                if colspan is None:
                    col_dim.append(1)
                else:
                    col_dim.append(int(colspan))
                col_dim_counter += 1

                rowspan = col.get("rowspan")
                if rowspan is None:
                    row_dim.append(1)
                else:
                    row_dim.append(int(rowspan))
                row_dim_counter += 1

                # Adjust column counter
                if col_counter == -1:
                    col_counter = 0
                else:
                    col_counter = col_counter + col_dim[col_dim_counter - 1]

                while skip_index[col_counter] > 0:
                    col_counter += 1

                # Get cell contents
                cell_data = col.get_text().encode('ascii', 'replace').replace('\n', '').replace('?', ' ')

                # Insert data into cell
                df.iat[row_counter, col_counter] = cell_data

                # Record column skipping index
                if row_dim[row_dim_counter] > 1:
                    this_skip_index[col_counter] = row_dim[row_dim_counter]

        # Adjust row counter
        row_counter += 1

        # Adjust column skipping index
        skip_index = [i - 1 if i > 0 else i for i in this_skip_index]

    # Append dataframe to list of tables
    tables_html.append(df)

    return (df)


def get_tables(htmldoc):
    soup = BeautifulSoup(htmldoc.content, 'html.parser')
    h2 = soup.find_all('h2')
    title = []
    for v in h2:
        t = v.getText()
        title.append(t)
    return soup.find_all('table'), title


def createdirectory(DBF_dir):
    if not os.path.exists(DBF_dir):
        os.mkdir(DBF_dir)
        print "created directory {0}".format(DBF_dir)


start_time = datetime.datetime.now()
print "Start Time: " + start_time.ctime()

today = datetime.datetime.today()
date = today.strftime('%Y%m%d')

createdirectory(outlocation+os.sep+'NMFS')
outlocation = outlocation+os.sep+'NMFS'
# Download and parse website table
r = requests.get(url)

list_tables, title = get_tables(r)
print title
for n in range(0, len(list_tables)):

    ssa = tables_read(list_tables, n)
    ssa.columns = ssa.iloc[0]
    ssa= ssa.reindex(ssa.index.drop(0))
    print ssa

    ssa['Common Name'] = ssa['Species'].map(
        lambda x: str(x.split('(')[0].split(',')[1]).strip() + " " + str(x.split('(')[0].split(',')[0]).strip() if len(
            x.split('(')[0].split(',')) >= 2 else str(x.split('(')[0].split(',')[0]))
    ssa['Scientific Name'] = ssa['Species'].map(lambda x: x if len(x.split('(')) <= 1 else (
        str(x.split('(')[1]).replace(')', '').strip()) if len(x.split('(')) == 2 else str(
        (x.split('(')[2]).split(')')[0]).replace(')', '').strip())
    ssa['Population Name'] = ssa['Species'].map(lambda x: '' if len(x.split('(')) <= 1 else (
        '' if len(x.split('(')) == 2 else str(x.split('(')[2]).split(')')[1]).replace(')', '').strip())
    row_count = 1
    year_col = [v for v in ssa.columns.values.tolist() if v.startswith('Year')]

    while row_count <= len(ssa):
        try:
            if float(ssa.ix[row_count,(year_col[0])]) > 0:
                ssa.ix[row_count,'Group'] = group
                row_count +=1
            else:
                group = ssa.ix[row_count,'Species']
                row_count +=1
        except ValueError:  # white space character in one of the cells from online table can't be converted to float
                group = ssa.ix[row_count,'Species']
                row_count +=1
    ssa['Group'].fillna(0, inplace =True)
    remove_blanks = ssa.loc[ssa['Group'] != 0]
    remove_foreign = remove_blanks[remove_blanks['Scientific Name'].isin(removed_perNMFS) == False]

    remove_foreign.to_csv(outlocation + os.sep + 'FilteredWebsite_NMFS_'+ title[n].split('(')[0] +"_"+ date + '.csv', encoding='utf-8')
    ssa.to_csv(outlocation + os.sep + 'FullWebsite_NMFS_'+ title[n].split('(')[0] +"_" + date + '.csv', encoding='utf-8')

end = datetime.datetime.now()
print "End Time: " + end.ctime()
elapsed = end - start_time
print "Elapsed  Time: " + str(elapsed)
