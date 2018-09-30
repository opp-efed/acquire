# -*- coding: utf-8 -*-
"""
Created on Wed Jul 18 08:46:24 2018

@author: mweber
"""
import pandas as pd
import glob
import os
from scipy import stats

def my_csv_reader(path):
    d = pd.read_csv(path, skiprows=5,header=None, names=["Daily Depth (m)", "avg","pore water", "peak"])
    d['Date'] = pd.date_range(start='1/1/1961', end='12/31/1990')  # an example of a column to be added to each dataframe
    return d

def get_n_largest(matrix, n):
    return matrix.drop_duplicates().sort_values(ascending=False)

def main():
    # Input paths and variables
#    input_dir = 'H:/WorkingData/OPP_Detail/ExcelMacro/InputTables'
    input_dir = 'H:/WorkingData/OPP_Detail/ExcelMacro/support files/step 2'
    filenames = [f for f in os.listdir(input_dir) if f.count('run')]
    hucs = [h.split('_')[3][-1:] for h in filenames]
    hucs = list(set([huc for huc in hucs]))
    Area_fractions = [1,1,1] # Add more flexibility later
    # Loop through HUCs and create separate excel file for each HUC output
    for HUC in hucs:
        outfile = 'H:/WorkingData/OPP_Detail/testProcessed_python_HUC_' + HUC + '.xlsx'
        writer = pd.ExcelWriter(outfile, engine='xlsxwriter')
        # Loop through Bin values and create separate worksheet for each bin
        for Bin in ['2','4','7']:
            # Loop through the three scenarios for each Bin worksheet
            for Scenario in ['Impervious','Residential','ROW']:  # Add more flexibility later             
                print('on HUC ' + HUC + ' on Bin ' + Bin + ' and Scenario ' + Scenario)
                df = pd.concat([my_csv_reader(f) for f in glob.glob(input_dir + '/*_' + Bin + '_' + Scenario + 'ESA' + HUC + '*.csv')])
                # convert from kg/m3 to ppm
                df[["avg","pore water", "peak"]] = df[["avg","pore water", "peak"]] * 1000
                df = df.groupby('Date')["avg","pore water", "peak"].mean()
                df = df.reset_index()
                if Scenario == 'Impervious':
                    final = df.copy()
                    final.columns.values[[1,2,3]] = ['avg ' + Scenario + ' conc.ppm', 'pore water ' + Scenario + ' conc.ppm',
                                        'peak ' + Scenario + ' conc.ppm']
                    final['Year'] = final.Date.apply(lambda x: pd.to_datetime(x).strftime('%Y'))
                    final = final.reset_index()
                    final = final.filter(['Date','Year','avg ' + Scenario + ' conc.ppm', 'pore water ' + Scenario + ' conc.ppm',
                                        'peak ' + Scenario + ' conc.ppm'], axis=1)
                if Scenario != 'Impervious':
                    df.columns.values[[1,2,3]] = ['avg ' + Scenario + ' conc.ppm', 'pore water ' + Scenario + ' conc.ppm',
                                        'peak ' + Scenario + ' conc.ppm']
                    df = df.copy()
                    df = df.filter(['Date','avg ' + Scenario + ' conc.ppm', 'pore water ' + Scenario + ' conc.ppm',
                                        'peak ' + Scenario + ' conc.ppm'], axis=1)
                    final = pd.merge(final, df, on='Date')
                    print(final.shape)
            # Assemble final values for each Bin worksheet
            final['Date'] = final.Date.apply(lambda x: pd.to_datetime(x).strftime('%m/%d/%Y'))
            # Fold in summary statistics
            final['Adjusted Peak EEC (ppm)'] = (final['peak Impervious conc.ppm'] \
                  * Area_fractions[0]) + (final['peak Residential conc.ppm'] \
                                  * Area_fractions[1]) + (final['peak ROW conc.ppm'] \
                  * Area_fractions[2])
            final['Adjusted Average AEEC (ppm)'] = (final['avg Impervious conc.ppm'] \
                  * Area_fractions[0]) + (final['avg Residential conc.ppm'] \
                                  * Area_fractions[1]) + (final['avg ROW conc.ppm'] \
                  * Area_fractions[2])
            final['4 day'] = final.rolling(window=4)['Adjusted Average AEEC (ppm)'].mean()
            final['14 day'] = final.rolling(window=14)['Adjusted Average AEEC (ppm)'].mean()
            final['21 day'] = final.rolling(window=21)['Adjusted Average AEEC (ppm)'].mean()
            final['30 day'] = final.rolling(window=30)['Adjusted Average AEEC (ppm)'].mean()
            final['60 day'] = final.rolling(window=60)['Adjusted Average AEEC (ppm)'].mean()
            final['90 day'] = final.rolling(window=90)['Adjusted Average AEEC (ppm)'].mean()
            final['Annual'] = final.rolling(window=365)['Adjusted Average AEEC (ppm)'].mean()
            final['PW_peak'] = (final['pore water Impervious conc.ppm'] \
                  * Area_fractions[0]) + (final['pore water Residential conc.ppm'] \
                                  * Area_fractions[1]) + (final['pore water ROW conc.ppm'] \
                  * Area_fractions[2])
            final['PW_21'] = final.rolling(window=21)['PW_peak'].mean()
            final['year'] = pd.Series(range(1961, 1991)).astype(int).astype(str)
            final['Max Peak'] = pd.Series(final.groupby('Year')['Adjusted Peak EEC (ppm)'].max().values)
            final['1-day'] = pd.Series(final.groupby('Year')['Adjusted Average AEEC (ppm)'].max().values)
            final['annual'] = pd.Series(final.groupby('Year')['Annual'].max().values)
            final['4-day'] = pd.Series(final.groupby('Year')['4 day'].max().values)
            final['Max 21 day'] = pd.Series(final.groupby('Year')['21 day'].max().values)
            final['Max 60 day'] = pd.Series(final.groupby('Year')['60 day'].max().values)
            final['Max 90 day'] = pd.Series(final.groupby('Year')['90 day'].max().values)
            final['Max PW'] = pd.Series(final.groupby('Year')['PW_peak'].max().values)
            final['Max PW 21'] = pd.Series(final.groupby('Year')['PW_21'].max().values)
            
            #Add final summary numbers table
            final.insert(loc=32, column='', value = '')
            final.insert(loc=33, column='Prob', value = '')
            final.loc[0,"Prob"] = 1/(30+1)
            final.loc[1,"Prob"] = (1/(30+1)) *2
            final.loc[2,"Prob"] = (1/(30+1)) *3
            final.loc[3,"Prob"] = (1/(30+1)) *4
            
            final.loc[5,"Prob"] = '1-in-10 yr (ppm)'
            final.loc[6,"Prob"] = '1-in-15 yr (ppm)'
            final.loc[7,"Prob"] = '1-in-10 yr (ppb)'
            final.loc[8,"Prob"] = '1-in-15 yr (ppb)'
            
            final.insert(loc=34, column='Max Peak Summary', value = '')
            final.loc[0:3,"Max Peak Summary"] = final['Max Peak'].nlargest(4).values
            final.insert(loc=35, column='1-day Summary', value = '')
            final.loc[0:3,"1-day Summary"] = final['1-day'].nlargest(4).values
            final.insert(loc=36, column='Annual Summary', value = '')
            final.loc[0:3,"Annual Summary"] = final['Annual'].nlargest(4).values
            final.insert(loc=37, column='4-Day Summary', value = '')
            final.loc[0:3,"4-Day Summary"] = final['4-day'].nlargest(4).values
            final.insert(loc=38, column='Max 21 day Summary', value = '')
            final.loc[0:3,"Max 21 day Summary"] = final['Max 21 day'].nlargest(4).values
            final.insert(loc=39, column='Max 60 day Summary', value = '')
            final.loc[0:3,"Max 60 day Summary"] = final['Max 60 day'].nlargest(4).values
            final.insert(loc=40, column='Max 90 day Summary', value = '')
            final.loc[0:3,"Max 90 day Summary"] = final['Max 90 day'].nlargest(4).values
            final.insert(loc=41, column='Max PW Summary', value = '')
            final.loc[0:3,"Max PW Summary"] = final['Max PW'].nlargest(4).values
            final.insert(loc=42, column='Max PW 21 Summary', value = '')
            final.loc[0:3,"Max PW 21 Summary"] = final['Max PW 21'].nlargest(4).values
            
            #Max Peak 1-in-10 and 1-in-15 numbers
            slope, intercept = stats.linregress(final.loc[2:3,'Prob'].values.astype(float), final.loc[2:3,
                                                'Max Peak Summary'].values.astype(float))[0:2]
            final.loc[5,"Max Peak Summary"] = slope * 0.1 + intercept
            slope, intercept = stats.linregress(final.loc[1:2,'Prob'].values.astype(float), final.loc[1:2,
                                                'Max Peak Summary'].values.astype(float))[0:2]
            final.loc[6,"Max Peak Summary"] = slope * 0.067 + intercept
            final.loc[7,"Max Peak Summary"] = final.loc[5,"Max Peak Summary"] * 1000
            final.loc[8,"Max Peak Summary"] = final.loc[6,"Max Peak Summary"] * 1000
            
            #1-dqy 1-in-10 and 1-in-15 numbers
            slope, intercept = stats.linregress(final.loc[2:3,'Prob'].values.astype(float), final.loc[2:3,
                                                '1-day Summary'].values.astype(float))[0:2]
            final.loc[5,"Max Peak Summary"] = slope * 0.1 + intercept
            slope, intercept = stats.linregress(final.loc[1:2,'Prob'].values.astype(float), final.loc[1:2,
                                                '1-day Summary'].values.astype(float))[0:2]
            final.loc[6,"1-day Summary"] = slope * 0.067 + intercept
            final.loc[7,"1-day Summary"] = final.loc[5,"1-day Summary"] * 1000
            final.loc[8,"1-day Summary"] = final.loc[6,"1-day Summary"] * 1000
            
            #4-dqy 1-in-10 and 1-in-15 numbers
            slope, intercept = stats.linregress(final.loc[2:3,'Prob'].values.astype(float), final.loc[2:3,
                                                '4-Day Summary'].values.astype(float))[0:2]
            final.loc[5,"4-Day Summary"] = slope * 0.1 + intercept
            slope, intercept = stats.linregress(final.loc[1:2,'Prob'].values.astype(float), final.loc[1:2,
                                                '4-Day Summary'].values.astype(float))[0:2]
            final.loc[6,"4-Day Summary"] = slope * 0.067 + intercept
            final.loc[7,"4-Day Summary"] = final.loc[5,"4-Day Summary"] * 1000
            final.loc[8,"4-Day Summary"] = final.loc[6,"4-Day Summary"] * 1000
            
            #Max 21 dqy 1-in-10 and 1-in-15 numbers
            slope, intercept = stats.linregress(final.loc[2:3,'Prob'].values.astype(float), final.loc[2:3,
                                                'Max 21 day Summary'].values.astype(float))[0:2]
            final.loc[5,"Max 21 day Summary"] = slope * 0.1 + intercept
            slope, intercept = stats.linregress(final.loc[1:2,'Prob'].values.astype(float), final.loc[1:2,
                                                'Max 21 day Summary'].values.astype(float))[0:2]
            final.loc[6,"Max 21 day Summary"] = slope * 0.067 + intercept
            final.loc[7,"Max 21 day Summary"] = final.loc[5,"Max 21 day Summary"] * 1000
            final.loc[8,"Max 21 day Summary"] = final.loc[6,"Max 21 day Summary"] * 1000
            
            #Max 60 dqy 1-in-10 and 1-in-15 numbers
            slope, intercept = stats.linregress(final.loc[2:3,'Prob'].values.astype(float), final.loc[2:3,
                                                'Max 21 day Summary'].values.astype(float))[0:2]
            final.loc[5,"Max 60 day Summary"] = slope * 0.1 + intercept
            slope, intercept = stats.linregress(final.loc[1:2,'Prob'].values.astype(float), final.loc[1:2,
                                                'Max 60 day Summary'].values.astype(float))[0:2]
            final.loc[6,"Max 60 day Summary"] = slope * 0.067 + intercept
            final.loc[7,"Max 60 day Summary"] = final.loc[5,"Max 60 day Summary"] * 1000
            final.loc[8,"Max 60 day Summary"] = final.loc[6,"Max 60 day Summary"] * 1000
            
            #Max 90 dqy 1-in-10 and 1-in-15 numbers
            slope, intercept = stats.linregress(final.loc[2:3,'Prob'].values.astype(float), final.loc[2:3,
                                                'Max 21 day Summary'].values.astype(float))[0:2]
            final.loc[5,"Max 90 day Summary"] = slope * 0.1 + intercept
            slope, intercept = stats.linregress(final.loc[1:2,'Prob'].values.astype(float), final.loc[1:2,
                                                'Max 90 day Summary'].values.astype(float))[0:2]
            final.loc[6,"Max 90 day Summary"] = slope * 0.067 + intercept
            final.loc[7,"Max 90 day Summary"] = final.loc[5,"Max 90 day Summary"] * 1000
            final.loc[8,"Max 90 day Summary"] = final.loc[6,"Max 90 day Summary"] * 1000
            
            #Max PW 1-in-10 and 1-in-15 numbers
            slope, intercept = stats.linregress(final.loc[2:3,'Prob'].values.astype(float), final.loc[2:3,
                                                'Max 21 day Summary'].values.astype(float))[0:2]
            final.loc[5,"Max PW Summary"] = slope * 0.1 + intercept
            slope, intercept = stats.linregress(final.loc[1:2,'Prob'].values.astype(float), final.loc[1:2,
                                                'Max PW Summary'].values.astype(float))[0:2]
            final.loc[6,"Max PW Summary"] = slope * 0.067 + intercept
            final.loc[7,"Max PW Summary"] = final.loc[5,"Max PW Summary"] * 1000
            final.loc[8,"Max PW Summary"] = final.loc[6,"Max PW Summary"] * 1000
            
            #Max PW 21 1-in-10 and 1-in-15 numbers
            slope, intercept = stats.linregress(final.loc[2:3,'Prob'].values.astype(float), final.loc[2:3,
                                                'Max PW 21 Summary'].values.astype(float))[0:2]
            final.loc[5,"Max PW 21 Summary"] = slope * 0.1 + intercept
            slope, intercept = stats.linregress(final.loc[1:2,'Prob'].values.astype(float), final.loc[1:2,
                                                'Max PW 21 Summary'].values.astype(float))[0:2]
            final.loc[6,"Max PW 21 Summary"] = slope * 0.067 + intercept
            final.loc[7,"Max PW 21 Summary"] = final.loc[5,"Max PW 21 Summary"] * 1000
            final.loc[8,"Max PW 21 Summary"] = final.loc[6,"Max PW 21 Summary"] * 1000
            
            final.loc[10,"Prob"] = 'Average Annual (ppb)'
            final.loc[10,"4-Day Summary"] = final['Annual'].mean() * 1000
            final.to_excel(writer, sheet_name='Bin ' + Bin, index=False)
        writer.save()
main()

