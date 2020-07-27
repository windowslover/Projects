#-------------------------------------------------------------------------------
# Name:        Property Appraisal Protest
#
# Purpose:     Download Hays Central Appraisal District datafiles with property info to include property ID, neighborhood code, and appraise value.
#              Combine street/year pair files together.
#              Compute percent increase in value from one year to the next to check a home's value against statistics like the median increase and visualize in GIS.
#
# Author:      Jason Bartling
#
# Created:     05/13/2020
# Last Updated:  07/26/2020
#
# Copyright:   (c) Jason 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import pandas
import os
import requests
import time

# Take in parameters.  If none are entered for streetsCSV and downloadDir provide default values
def userInput():

    streetsCSV = input('Please enter path to csv with street name lookup table: ').replace('\\','/')

    if len(streetsCSV) == 0:
        streetsCSV = 'C:/Users/jason/Documents/QGISstuff/Geocoding/BishopsCrossingStreets.csv'

    downloadDir = input('Please enter path to download directory for appraisal files: ').replace('\\','/')

    if len(downloadDir) == 0:
        downloadDir = 'C:/Users/jason/Documents/QGISstuff/Geocoding/CAD-Docs/Bishops Crossing2'

    prevYear = input('Please enter previous appraisal year: ')

    if len(prevYear) == 0:
        prevYear = 2019

    currYear = input('Please enter current appraisal year: ')

    if len(currYear) == 0:
        currYear = 2020

    return streetsCSV, downloadDir, prevYear, currYear


# Download appraisal files by street and neighborhood code for both the current and previous year using dataframe of neighborhood codes and street names
def downloadFiles(prevYear, currYear, streetsCSV, downloadDir):

    #load in dataframe of streetnames and neighborhood codes
    print ('Downloading Hays CAD files...')
    df = pandas.read_csv(streetsCSV)

    yearList = [prevYear, currYear]

    # Get neighborhood codes and street names for use in the request url
    for i in range(len(df)):

    #nCode = 'BISH'
        nCode = df.loc[i]['Neighborhood Code']
        stn = df.loc[i]['STN']

        for year in yearList:

            url = 'https://esearch.hayscad.com/Search/SearchResultDownload?keywords=NeighborhoodCode:{}%20Year:{}%20StreetName:{}'.format(nCode, year,stn)

            r = requests.get(url, allow_redirects=True)

            filePath = os.path.join(downloadDir, '{}_{}_{}.csv'.format(nCode, stn, year))

            ## May need to check response type first
            open(filePath, 'wb').write(r.content)

            time.sleep(.002)

    print ('Done downloading files')



# Merge dataframes together that have the same columns
def mergeDataframes(dataframeList):

    mergeDF = pandas.concat(dataframeList, ignore_index =True)

    return mergeDF


# Drop a list of columns from a dataframe
def dropColumns(dataFrame, columnsToKeep):

    columnsToDelete = []

    for item in list(dataFrame.columns):

        if item not in columnsToKeep:

            columnsToDelete.append(item)

    #print ('Columns to delete are {}'.format(columnsToDelete))

    dataFrame.drop(columns = columnsToDelete, axis = 'columns' , inplace = True)


# Take a list of column names and their new names from two separate lists to rename using dict mapping
def renameColumns(dataFrame, columnNameList, newNameList):

    renameDict = {}

    # Loop through key value pairs using index for each list and set dict
    for i in range(len(columnNameList)):

        #renameDict = {columnNameList[i] : newNameList[i]}
        keyVal = {columnNameList[i] : newNameList[i]}
        renameDict.update(keyVal)

    dataFrame.rename(columns = renameDict, inplace = True)

#  Get list of files to process using a directory as input
def getListOfFiles(fileDir):

    dirItems = os.listdir(fileDir)

    fileList = []

    for item in dirItems:

        if not os.path.isdir(os.path.join(fileDir, item)):

            fileList.append(os.path.join(fileDir, item))

    return fileList

## Need csvt with datatypes in order for PctIncr to get loaded in as a number in QGIS
def calculcatePctInrc(prevYear, currYear, dataFrame):

    dataFrame['PctIncr'] = (((dataFrame['{}_Appraisal'.format(currYear)] / dataFrame['{}_Appraisal'.format(prevYear)]) - 1) * 100)

    dataFrame['PctIncr'] = dataFrame['PctIncr'].values.astype(float).round(2)

def main(downloadDir, prevYear, currYear, streetsCSV):

    #columnsToKeep = ['Property ID','Neighborhood Code','Appraised Value']
    columnsToKeep = ['Quick Ref ID','Neighborhood Code','Appraised Value']

    # Download appraisal files
    downloadFiles(prevYear, currYear, streetsCSV, downloadDir)

    # Go through directory to get a list of all the files to process
    fileList = getListOfFiles(downloadDir)

    prevYearDfList = []
    currYearDfList = []

    for file in fileList:

        df = pandas.read_csv(file)


        print ('Dropping extra columns...')
        dropColumns(df, columnsToKeep)

        #Get year to use in column name by breaking down path into basename and filename
        baseName = os.path.basename(file)
        fileName = os.path.splitext(baseName)[0]

        # Rename the columns that need to change
        year = fileName[-4:]
        columnsToRename = ['Appraised Value', 'Quick Ref ID']
        newColumnNames = ['{}_Appraisal'.format(year), 'Property ID']

        print ('Renaming columns...')
        renameColumns(df, columnsToRename, newColumnNames)

        if int(year) == prevYear:
            prevYearDfList.append(df)

        if int(year) == currYear:
            currYearDfList.append(df)

    # Merge current year files to each other, and the same for previous year
    prevYearMergedDF = mergeDataframes(prevYearDfList)

    currYearMergedDF = mergeDataframes(currYearDfList)

    #  Need to make directory if it doesn't already exist
    if  os.path.isdir(os.path.join(downloadDir, 'summary')) == False:
        os.mkdir(os.path.join(downloadDir, 'summary'))

    outFolder = os.path.join(downloadDir, 'summary')

    outFilePrevYear = '{}merged.csv'.format(prevYear)
    PrevYearPath = os.path.join(outFolder, outFilePrevYear)

    outFileCurrYear = '{}merged.csv'.format(currYear)
    CurrYearPath = os.path.join(outFolder, outFileCurrYear)

    outfileCombined = '{}_{}combined.csv'.format(prevYear, currYear)
    CombinedPath = os.path.join(outFolder, outfileCombined)

    csvtName = '{}_{}combined.csvt'.format(prevYear, currYear)
    csvtPath = os.path.join(outFolder, csvtName)

    prevYearMergedDF.to_csv(PrevYearPath, index = False)
    currYearMergedDF.to_csv(CurrYearPath, index = False)

    # Join currYearMergedDF to prevYearMergedDF to add curr year appraisal value
    appraisalColumn = '{}_Appraisal'.format(str(currYear))

    ## If neighborhood code happens to be different across two years the join will fail
    ## Need to add code to replace previous year file with newer property ID if the 2 years happen to be different
    prevYearNCodes = list(prevYearMergedDF['Neighborhood Code'].unique())

    currYearNCodes = list(currYearMergedDF['Neighborhood Code'].unique())

    if len(prevYearNCodes) > 1:

        for nCode in prevYearNCodes:

            if nCode != currYearNCodes[0]:

                prevYearMergedDF = prevYearMergedDF.replace({nCode: currYearNCodes[0]})

    #prevYearNCodes = list(prevYearMergedDF['Neighborhood Code'].unique())

    #print('prevYearNCodes: {}'.format(prevYearNCodes))
    #print('currYearNCodes: {}'.format(currYearNCodes))


    print ('Joining appraisal years...')
    bothYearsMergeDF = pandas.merge(prevYearMergedDF,currYearMergedDF[['Property ID', appraisalColumn]],on= 'Property ID', how='left')

    # Calculate percent increase in appraisal value from one year to the next
    calculcatePctInrc(prevYear, currYear, bothYearsMergeDF)


    print ('Writing combined output file')
    bothYearsMergeDF.to_csv(CombinedPath, index = False)

    # Also write csvt file with datatypes for columns so it gets joined properly in QGIS
    dataTypes = '"String", "String", "Real(8,2)", "Real(8,2)", "Real(4,2)"'
    open(csvtPath, 'w').write(dataTypes)

    return bothYearsMergeDF

## Execute program code

streetsCSV, downloadDir, prevYear, currYear = userInput()

df = main(downloadDir, prevYear, currYear, streetsCSV)










