#-------------------------------------------------------------------------------
# Name:        Format Data File
# Purpose:     Replace countyName state in inputFile with state abbreviation for all counties
#
# Author:      Jason
#
# Created:     10/09/2018
# Copyright:   (c) Jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
    #import io
    import sys
    import traceback
    import xlrd
    #import xlwt
    #import re

    inputFileName="H:/GEO 4411/AtlasProject/DataSources/2016_Estimated_Post2001_Gulf_War_Vets.xls"

    #Remove previous extension and add new extension of .csv to outputFileName
    outputFileName=inputFileName[:-4]+'.csv'
    #outputFileName=inputFileName[:-4]+'_Updated.xls'

    #workbook = xlrd.open_workbook(inputFileName)
    inputWorkbook = xlrd.open_workbook(inputFileName)
    #worksheet = workbook.sheet_by_index(0)
    inputWorksheet = inputWorkbook.sheet_by_index(0)

    #States dict to match state name to abbreviation
    statesDict = {'Washington':'WA','Oregon':'OR','California':'CA','Idaho':'ID','Nevada':'NV','Arizona':'AZ','Utah':'UT','New Mexico':'NM','Colorado':'CO','Wyoming':'WY',
    'Montana':'MT','North Dakota':'ND','South Dakota':'SD','Nebraska':'NE','Kansas':'KS','Oklahoma':'OK','Texas':'TX','Louisiana':'LA','Arkansas':'AR','Missouri':'MO',
    'Iowa':'IA','Minnesota':'MN','Wisconsin':'WI','Illinois':'IL','Indiana':'IN','Michigan':'MI','Ohio':'OH','Kentucky':'KY','Tennessee':'TN','Mississippi':'MS',
    'Alabama':'AL','Florida':'FL','Georgia':'GA','South Carolina':'SC','North Carolina':'NC','Virginia':'VA','West Virginia':'WV','Maryland':'MD','Delaware':'DE','New Jersey':'NJ',
    'Pennsylvania':'PA','New York':'NY','Connecticut':'CT','Rhode Island':'RI','Massachusetts':'MA','Vermont':'VT','New Hampshire':'NH','Maine':'ME','Alaska':'AK','Hawaii':'HI',
    'District of Columbia':'DC'}

    print 'Opening input file...'

    #outFile = io.open(outputFileName,'w',encoding='utf-8')
    outFile = open(outputFileName,'w')
    #outputWorkbook = xlwt.Workbook()
    #outputWorksheet = outputWorkbook.add_sheet("Sheet1")

    #Write header record
    for row in range(0,1):
        for col in range(0,inputWorksheet.ncols):
            #Write a comma after value until last header record
            if col < inputWorksheet.ncols - 1:

                #print "Column number: {} Value: {}".format(col,inputWorksheet.cell(row,col).value)
                outFile.write('"{}",'.format(inputWorksheet.cell(row,col).value))


            else:
                #print "Column number: {} Value: {} No Comma After".format(col,inputWorksheet.cell(row,col).value)
                outFile.write(inputWorksheet.cell(row,col).value)
            #outputWorksheet.write(row,col,inputWorksheet.cell(row,col).value)

    outFile.write('\n')

    print 'Done writing header record for {}'.format(outputFileName)

    #outputWorkbook.save(outputFileName)

    #return

    countyName=''
##    personalIncome=0
    numRows=0
    countyNamesUpdated=0
    numSkipped=0

    outputRow = 2
    #Start on 2rd row since 1st row is header
    print 'Input worksheet total rows including header: {}'.format(inputWorksheet.nrows)
    print 'Input worksheet total cols: {}'.format(inputWorksheet.ncols)

    for row in range(1,inputWorksheet.nrows):

        recordSkipped=False

        for col in range(0,inputWorksheet.ncols):
            #Update county name for first column
            if col == 0:

                #Get value of the countyName cell
                countyName=inputWorksheet.cell(row,col).value

                #Replace county in county name with empty string
                countyName=countyName.replace('County','')
                countyName=countyName.replace('Parish','')
                countyName=countyName.replace('city','')

                #find comma position in countyName
                countyNameCommaPos=countyName.find(',')

                #Get state name from countyName using comma position + 2 as starting point
                countyStateName = countyName[countyNameCommaPos+2:]

                #Only process contiguous US
                if countyStateName not in ['Alaska']:


                    #Get state abbreviation from statesDict
                    countyStateAbbrev = statesDict[countyStateName]

                    #Reformat countyName field to have stateAbbrev instead of stateName
                    countyName=countyName[:countyNameCommaPos-1]+', {}'.format(countyStateAbbrev)
                    #print 'CountyName:  {}'.format(countyName.encode('utf-8'))

                    try:
                        #outputWorksheet.write(outputRow,col,countyName)

                        outFile.write('"{}",'.format(countyName.encode('utf-8')))
                        #outFile.write('"{}",'.format(countyName))
                    except:
                        tb = sys.exc_info()[2]
                        tbinfo = traceback.format_tb(tb)[0]
                        print "An error has occurred\n"
                        pymsg = "PYTHON ERRORS:\nTraceback info\n" + tbinfo + "\nError Info:\n" + str(sys.exc_type) + ":" + str(sys.exc_value) + "\n"
                        print pymsg
                        print 'CountyName: {} Row: {}'.format(countyName.encode('utf-8'),outputRow)

                    countyNamesUpdated+=1
                #For exclusions stop processing the remaining columns
                else:
                    recordSkipped=True
                    numSkipped+=1
                    break

            #For other columns after countyName
            else:
                #Add comma after cell value until last column
                if col < inputWorksheet.ncols - 1:
                    #print "Column number: {} Value: {}".format(col,inputWorksheet.cell(row,col).value)
                    outFile.write('{},'.format(inputWorksheet.cell(row,col).value))
                else:
                    #print "Column number: {} Value: {} No Comma".format(col,inputWorksheet.cell(row,col).value)
                    outFile.write(str(inputWorksheet.cell(row,col).value))

                #Check value of cell to see if its a number if it is cast it as an int
                #cellValue=inputWorksheet.cell(row,col).value
                #print 'CellValue: '.format(inputWorksheet.cell(row,col).value)
                #print 'CellValue Type: '.format(str(type(cellValue)))


                #match = re.search('^[0-9]+.0$',str(cellValue))

                #If inputSpreadsheet cell value is a number format it as such for the new outputSpreadsheet
                #if match != None:
                  #style= xlwt.XFStyle()
                  #style.num_format_str = '0'
                  #outputWorksheet.write(outputRow,col,cellValue,style)
                #else:
                    #outputWorksheet.write(outputRow,col,cellValue)



        #Add new line character after all columns in a row have been written
        if recordSkipped == False:
            outputRow+=1
            outFile.write('\n')
            numRows+=1

    #print 'The number of rows is %d' %(numRows)
    print 'The number of countyNames updated is %d' %(countyNamesUpdated)
    print 'The number of records skipped is {}'.format(numSkipped)
    print 'Done writing to {0}'.format(outputFileName)

    outFile.close()
    #outputWorkbook.save(outputFileName)



if __name__ == '__main__':
    main()
