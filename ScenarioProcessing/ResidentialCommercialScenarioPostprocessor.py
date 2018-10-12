# -*- coding: utf-8 -*-
"""
Created on Wed Jul 18 08:46:24 2018

@author: mweber
"""

#======================
# imports
#======================

import pandas as pd
import glob
import os
from scipy import stats
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askdirectory

path = []

def Choose_Path():    
    tk.Tk().withdraw()
    path.append(askdirectory())
    
def CloseGUI():
    win.quit()
    win.destroy()

win = tk.Tk()   

# Add a title to gui      
win.title("PWC Non-Ag Post-Processor Inputs")

# Get directory
browser = ttk.Button(win, text = "Select main directory of PWC files", command=Choose_Path)
browser.grid(column=0, row=0,sticky=tk.W, pady=10)

# Get output directory
browser = ttk.Button(win, text = "Choose output directory", command=Choose_Path)
browser.grid(column=0, row=1,sticky=tk.W, pady=10)

# Get Preface
PrefaceLabel = ttk.Label(win, text="Add preface to timeseries names")
PrefaceLabel.grid(column=0, row=2)
Preface = tk.StringVar()
PrefaceEntered = ttk.Entry(win, width=12, textvariable=Preface)
PrefaceEntered.grid(column=1, row=2)

# Checkboxes for Impervious, Residential, ROW
chImp = tk.IntVar()
check1 = tk.Checkbutton(win, text="Include Impervious Runs?", variable=chImp, state='active')
check1.select()
check1.grid(column=0, row=3, sticky=tk.W)                   

chRes = tk.IntVar()
check2 = tk.Checkbutton(win, text="Include Residential Runs?", variable=chRes, state='active')
check2.select()
check2.grid(column=1, row=3, sticky=tk.W)                   

chRow = tk.IntVar()
check3 = tk.Checkbutton(win, text="Include ROW Runs?", variable=chRow, state='active')
check3.select()
check3.grid(column=2, row=3, sticky=tk.W) 


# Area Fractions for Impervious, Residential, ROW
labelsFrame1 = ttk.LabelFrame(win) 
labelsFrame1.grid(column=0, row=4)
AreaFracLab1 = ttk.Label(labelsFrame1, text="Area fraction")
AreaFracLab1.grid(column=0, row=0, sticky=tk.W)
AreaFrac1 = tk.StringVar()
nameEntered = ttk.Entry(labelsFrame1, width=5, textvariable=AreaFrac1)
nameEntered.grid(column=1, row=0, sticky=tk.W)

labelsFrame2 = ttk.LabelFrame(win) 
labelsFrame2.grid(column=1, row=4)
AreaFracLab2 = ttk.Label(labelsFrame2, text="Area fraction")
AreaFracLab2.grid(column=0, row=0, sticky=tk.W)
AreaFrac2 = tk.StringVar()
nameEntered = ttk.Entry(labelsFrame2, width=5, textvariable=AreaFrac2)
nameEntered.grid(column=1, row=0, sticky=tk.W)

labelsFrame3 = ttk.LabelFrame(win) # 1
labelsFrame3.grid(column=2, row=4)
AreaFracLab3 = ttk.Label(labelsFrame3, text="Area fraction")
AreaFracLab3.grid(column=0, row=0, sticky=tk.W)
AreaFrac3 = tk.StringVar()
nameEntered = ttk.Entry(labelsFrame3, width=5, textvariable=AreaFrac3)
nameEntered.grid(column=1, row=0, sticky=tk.W)

b1 = ttk.Button(win, text='Submit', command = CloseGUI).grid(column=1, sticky=tk.S)
win.mainloop()


def my_csv_reader(path, start_date, end_date, input_cols):
    d = pd.read_csv(path, skiprows=5,header=None, names=input_cols)
    d['Date'] = pd.date_range(start=start_date, end=end_date)  # an example of a column to be added to each dataframe
    return d

def get_n_largest(matrix, n):
    return matrix.drop_duplicates().sort_values(ascending=False)

def main():
    # Input paths and variables
#    input_dir = 'H:/WorkingData/OPP_Detail/ExcelMacro/InputTables'
    input_dir = path[0]
    output_dir = path[1]
    start_date = '1/1/1961'
    end_date = '12/31/1990'
    input_cols = ["Daily Depth (m)", "avg","pore water", "peak"]
    Area_fractions = [float(AreaFrac1.get()), float(AreaFrac2.get()), float(AreaFrac3.get())] # Add more flexibility later
    Bins = ['2','4','7']
    Scenarios = []
    if chImp.get() == 1:
        Scenarios.append('Impervious')
    if chRes.get() == 1:
        Scenarios.append('Residential')
    if chRow.get() == 1:
        Scenarios.append('ROW')
        
    filenames = [f for f in os.listdir(input_dir) if f.count('run')]
    hucs = [h.split('_')[3][-1:] for h in filenames]
    hucs = list(set([huc for huc in hucs]))
    
    # Loop through HUCs and create separate excel file for each HUC output
    for HUC in hucs:
        outfile = output_dir + '/testProcessed_python_HUC_' + HUC + '.xlsx'
        writer = pd.ExcelWriter(outfile, engine='xlsxwriter')
        # Loop through Bin values and create separate worksheet for each bin
        for Bin in Bins:
            # Loop through the three scenarios for each Bin worksheet
            for Scenario in Scenarios:  # Add more flexibility later             
                print('on HUC ' + HUC + ' on Bin ' + Bin + ' and Scenario ' + Scenario)
                df = pd.concat([my_csv_reader(f, start_date, end_date, input_cols) for f in glob.glob(input_dir + '/*_' + Bin + '_' + Scenario + 'ESA' + HUC + '*.csv')])
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

