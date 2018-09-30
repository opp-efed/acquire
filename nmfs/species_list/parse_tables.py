import os
import pandas as pd
import re
import requests
from datetime import datetime

class Table(object):
    def __init__(self, table_match):
        self.name = table_match.group(1)
        self.contents = table_match.group(2)

        # Parse table contents
        self.table = self.parse_table()

        # Detect subspecies
        self.detect_subspecies()

        # Get listing year
        self.listing_year()
        

    def detect_subspecies(self):
        self.table['Sublisting'] = None
        species_name = None
        species_num = 0
        self.table = self.table[self.table.Sublisting != "Parent"]
        for i, row in self.table.iterrows():
            if "<ul" in row.Species:
                row['Sublisting'] = re.sub(r"</?ul[^>]*?>", "", row.Species)
                row['Species'] = species_name
                self.table.loc[species_num, 'Sublisting'] = 'Parent'
            else:
                species_name = row.Species
                species_num = i

        self.table = self.table[self.table.Sublisting != "Parent"]

    def listing_year(self):
        for _, row in self.table.iterrows():
            if listing_type == 'listed':
                row['Year Listed'] = max(map(int, re.findall("\d{4}", row['Year Listed'])))
            elif listing_type == 'candidate':
                row['Year'] = max(map(int, re.findall("\d{4}", row['Year'])))

    def parse_table(self):
        row_pattern = r"<tr([^>]*)>([\s\S]+?)</tr>"
        cell_pattern = r"<t[dh]([^>]*)>([\s\S]*?)<\/t[dh]>"
        table = []
        family = None
        for row in re.finditer(row_pattern, self.contents):
            row_tag = row.group(1)
            row_contents = row.group(2)
            row = []
            for cell in re.finditer(cell_pattern, row_contents):
                cell_tag = cell.group(1)
                row.append(cell.group(2))

            # Detect 'family' headers
            skip = False
            if len(row) == 1:
                if "#d8d8d8" in row_tag or "#d8d8d8" in cell_tag:
                    family = row[0].strip()
                    skip = True
                else:
                    row += [''] * 4

            if not skip:
                if "class=\"blue\"" in row_tag:
                    row.append("Family")
                else:
                    row.append(family)
                table.append(row)
        return pd.DataFrame(data=table[1:], columns=table[0])
    
    def clean_table(self):

        
        if 'Sublisting' in list(self.table):
            self.table = self.table.rename(columns={'Sublisting' :  'Population'})            
        if 'Family' in list(self.table):
            self.table = self.table.rename(columns={'Family':'Sub Group'})           
        if 'Recovery Plan*' in list(self.table):
            self.table = self.table.rename(columns={'Recovery Plan*' :  'Recovery Plan'})            
        self.table['Common Name'] = self.table['Species'].map(lambda x: x.split('(')[0])
        self.table['Common Name'] = self.table['Common Name'].str.replace('<p>','')
        self.table['Common Name'] = self.table['Common Name'].str.replace('<u>','')
        self.table['Common Name'] = self.table['Common Name'].str.replace('</p>','')
        self.table['Common Name'] = self.table['Common Name'].str.replace('</u>','')
        self.table = self.table.loc[~self.table['Common Name'].str.contains('reinstated')==True]
        if self.table['Common Name'].str.contains(',').any():
            self.table['Common Name'] = self.table['Common Name'].map(lambda x: x.split(',')[0] if len(x.split(',')) ==1 else x.split(',')[1] + x.split(',')[0])         
        self.table['Scientific Name'] = self.table['Species'].map(lambda x: x.split('(')[2] if len(x.split('(')) >2 else x.split('(')[1]) 
        self.table['Scientific Name'] = self.table['Scientific Name'].map(lambda x: x.split(')')[0].replace(')', ''))             
        self.table['Population'] = self.table['Population'].fillna('')
        if filtered:# Filter foreign species and a couple other species not subject to section 7
            specific_list = ['Pristis pristis formerly P. perotteti', 'P. pristis', 'P. microdon']
            self.table = self.table.loc[self.table.Status.str.contains('F')==True]
            self.table = self.table.loc[~self.table.Status.isin(specific_list)==True]
        if not listing_type == 'Candidate':
            self.table = self.table[['Common Name','Scientific Name','Population','Sub Group','Year Listed','Status','Critical Habitat*',
                     'Recovery Plan']]    
        else:
            self.table = self.table[['Common Name','Scientific Name','Population','Sub Group','Year Listed']]      
    
    def save(self, output_dir):
        if filtered:
            out_name = self.name.split("(")[0].strip() + '_' + listing_type + '_filtered_'
        else:
            out_name = self.name.split("(")[0].strip() + '_' + listing_type + '_'
        date_stamp = datetime.strftime(datetime.now(), '%Y-%m-%d')    
        self.table.to_csv(os.path.join(output_dir, out_name) + date_stamp + '.csv',index = False)


class NMFS_Site(object):
    def __init__(self, site_url, local_site, overwrite):
        self.url = site_url
        self.local = local_site
        self.overwrite = overwrite

        # Pull site from NMFS if necessary
        self.site_string = self.acquire_site()

        # Clean up HTML formatting
        self.clean_site()

    def acquire_site(self):
        if self.overwrite or not os.path.exists(self.local):
            text = requests.get(self.url).text.encode('utf-8')
            with open(self.local, 'w') as f:
                f.write(text)
            with open(local_site, 'w') as f:
                f.write(text)
#            with open(local_site, 'w') as f:
#                f.write(text)    
        else:
            with open(self.local) as f:
                text = f.read()
        return text

    def extract_tables(self):
        table_pattern = r"<h2[^>]*?>(.+?)</h2>.+?<table[^>]*>([\s\S]+?)</table>"
        for table_match in re.finditer(table_pattern, self.site_string):
            table = Table(table_match)
            yield table

    def clean_site(self):
        self.site_string = re.sub(r"<br[^>]*?>", "", self.site_string)
        self.site_string = re.sub(r"</?a[^>]*?>", "", self.site_string)
        self.site_string = re.sub(r"</?b[^>]*?>", "", self.site_string)
        self.site_string = re.sub(r"</?em>", "", self.site_string)
        self.site_string = re.sub(r"</?i[^>]*?>", "", self.site_string)
        self.site_string = re.sub(r"</?li[^>]*?>", "", self.site_string)
        self.site_string = re.sub(r"</?span[^>]*?>", "", self.site_string)
        self.site_string = re.sub(r"</?div[^>]*?>", "", self.site_string)
        self.site_string = re.sub(r"\n", "", self.site_string)
        self.site_string = re.sub(r"&[a-z]+?;", "", self.site_string)
        self.site_string = re.sub(r"</?sup>", "", self.site_string)
        self.site_string = re.sub(r"</?strong>", "", self.site_string)

def stack_tables(path,tables):
    frame = pd.DataFrame()
    list_ = []
    for file in tables:
        if file.count('filtered'):
            append = '_filtered_'
        else:
            append = ''
        df = pd.read_csv(path + '/' + file)
        df['Group'] = file.split('.')[0]
        df = df[['Common Name','Scientific Name','Population','Group','Sub Group','Year Listed','Status','Critical Habitat*',
                     'Recovery Plan']]
        list_.append(df)
        frame = pd.concat(list_)
        frame.to_csv(path + '/' + listing_type + append + '.csv', index = False)

def main():
    listing_type = 'listed' # can change from listed to candidate
    filtered = False # write out filtered foreign species and a couple other species not subject to section 7
    site_url = 'http://www.nmfs.noaa.gov/pr/species/esa/' + listing_type + '.htm'
    local_site = os.path.join("bin", "listed.htm")
    output_dir = os.path.join("bin", "out_tables")
    overwrite = True

    nmfs_site = NMFS_Site(site_url, local_site, overwrite)

    for table in nmfs_site.extract_tables():
        table.clean_table()
        table.save(output_dir)
    
    # get specific lists of tables to stack to one table
    filtered_listed_tables = [x for x in os.listdir(output_dir) if x.count('filtered')]
    listed_tables = [x for x in os.listdir(output_dir) if not x.count('filtered')]
    
    stack_tables(output_dir, filtered_listed_tables)
    stack_tables(output_dir, listed_tables)
    
main()
