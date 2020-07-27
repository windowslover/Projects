#------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Name:        People Search
# Purpose:     Download demographic data for certain surname and zip code combinations using White Pages API
#
#Input:        File with surnames in one column and  zip codes in another
#              .Xslx (spreadsheet) input file most be formatted with last name in first column and zip code in second column both starting in the second row  (Sample file SmallSample.xslx)
#
#Output:       Demographic data in a .xls file (Output File Name textbox entry)
#              Note:  Only 100 person records appear to be included with each query even though the person count variable is much higher (May be due to White Pages Pro free trial)
#
# Author:      Jason Bartling
#
# Created:     09/05/2018
# Copyright:   (c) Jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


from Tkinter import *   #tkinter gui
import tkFileDialog #file dialog box for input file
import tkMessageBox #confirmation message box
import ttk    #Library for progress bar
import xlrd   #read excel spreadsheets
import xlwt   #write excel spreadsheets
import json   #parse json
import urllib2  #send http request
import os      #Check for output file existence
import sys      #Exception info
import traceback  #Exception info
from WhitePagesAPIKey import api_key   #api key for people search request
import threading #allow smooth display of output for user while GUI is active

class GUI(Frame):

    def __init__(self, master):
        Frame.__init__(self,master)
        self.grid()
        self.create_widgets()
        root.inputFileName = None
        root.outputFileName = None
        #root.overWriteResponse = None
        root.count = 0
        peoplethread= None

    #Create interactive elements on form
    def create_widgets(self):

        self.buttonInputFileChooser = Button(self, text = "Choose Input File")
        self.buttonInputFileChooser["command"] = self.select_file
        self.buttonInputFileChooser.grid(row = 0, column = 0, padx = 5, pady = 5)

        self.textFilePath = Text(self, width = 65, height = 1)
        self.textFilePath.grid(row = 0, column = 1)

        self.labelOutputFileName = Label(self, text = "Output File Name:")
        self.labelOutputFileName.grid(row = 1, column = 0)

        #Create output file textbox left aligned with sticky property W
        self.textOutputFileName = Text(self, width = 30, height = 1)
        self.textOutputFileName.grid(row = 1, column = 1, pady = 10, sticky= (W))

        self.buttonExecute = Button(self, text = "Search")
        #peoplethread = threading.Thread(target=self.people_search)
        self.buttonExecute["command"] = self.people_search
        #self.buttonExecute["command"] = peoplethread.start
        self.buttonExecute.grid(row = 2, column = 0, padx = 20, pady = 10 )


        self.textOutputWindow = Text(self, width = 65, height = 14)
        self.textOutputWindow.grid(row = 2, column = 1)

        #Tie scrollbar to output window text box
        self.scrollBar = Scrollbar(self, orient=VERTICAL, command=self.textOutputWindow.yview)

        #Use sticky property with N(orth) and S(outh) to allow scrollbar to scretch to fit next to the output window
        self.scrollBar.grid(row = 2, column = 2, sticky=(N,S), padx=5)

        #Tie output window text box to scroll bar
        self.textOutputWindow.configure(yscrollcommand=self.scrollBar.set)

        #Create as read only just for display purposes
        self.textOutputWindow.config(state=DISABLED)

        #** Progress bar not working may need to use threading??**
        #self.progressbar = ttk.Progressbar(self, orient=HORIZONTAL, length=490, mode='indeterminate')
        #self.progressbar.grid(row = 2, column = 1, sticky = (W), pady=10)



    #Select input file for people search and display path in textbox
    def select_file(self):
        root.inputFileName = tkFileDialog.askopenfilename(initialdir = "/", title = "Select File")

        self.textFilePath.insert (0.0, root.inputFileName)

        #Get the value of the textbox from line 1 character zero to the end of the textbox minus one character for newline
        #print self.textFilePath.get("1.0", 'end-1c')

    #Function to do the bulk of the people searching called from clicking the search button
    def people_search(self):

        #Clear OutputWindow text
        self.textOutputWindow.config(state=NORMAL)
        self.textOutputWindow.delete(1.0, END)
        self.textOutputWindow.config(state=DISABLED)

        overwriteResponse = False

        #Get the output file name
        root.outputFileName = self.textOutputFileName.get("1.0",'end-1c')

        #Check that input file has actually been selected to process
        if  root.inputFileName is None or root.inputFileName is '':
            self.textOutputWindow.config(state=NORMAL)
            self.textOutputWindow.insert (END, "No input file selected")
            self.textOutputWindow.config(state=DISABLED)
            return

        #Check that an output file name has been supplied
        elif root.outputFileName == '' or None:
                self.textOutputWindow.config(state=NORMAL)
                self.textOutputWindow.insert (END, "No output file name entered.  Please enter one.")
                self.textOutputWindow.config(state=DISABLED)
                return
        else:
            #Add extension to end of outputFileName
            root.outputFileName+='.xls'

            #Check with user before overwriting existing file
            if os.path.isfile(root.outputFileName):
                overwriteResponse = tkMessageBox.askyesno(message='%s already exists.  Are you sure you want to overwrite it?' %(root.outputFileName), icon='question', title='Overwrite')

            #If user chooses not to overwrite existing file prompt them to enter a new file name
            if overwriteResponse is False:
                self.textOutputWindow.config(state=NORMAL)
                self.textOutputWindow.insert (END, "Please enter another output file name to create a new file.")
                self.textOutputWindow.config(state=DISABLED)
                return

        #Create separate function to be handled as a thread so that GUI does not freeze
        def worker_thread():

            #Disable search button until done executing
            self.buttonExecute.config(state=DISABLED)

            #Open workbook and worksheet; Catch error for invalid file type if not excel spreadsheet
            try:
                workbook = xlrd.open_workbook(root.inputFileName)
                worksheet = workbook.sheet_by_index(0)
            except xlrd.XLRDError:
                self.textOutputWindow.config(state=NORMAL)
                self.textOutputWindow.insert (END, "ERROR:  Make sure input file is a .xls or .xlsx excel file")
                self.textOutputWindow.config(state=DISABLED)
                return

            #Initialize lists for last names and zip codes
            listLastName = []
            listZipCode = []

            #Quick check to see that input file is in proper format by looking at first two cells in header row
            if str(worksheet.cell(0,0).value).lower() != 'lastname' or str(worksheet.cell(0,1).value).lower() != 'zipcode':
                self.textOutputWindow.config(state=NORMAL)
                self.textOutputWindow.insert (END, "ERROR:  Check the input file for proper formatting.\n")
                self.textOutputWindow.insert (END, "Header for lastname and/or zipcode not found in cells 1 and 2.")
                self.textOutputWindow.config(state=DISABLED)
                return

            #Iterate over total rows in worksheet ignoring header row zero to create zipCode and lastName lists
            for row in range(1,worksheet.nrows):
                #Only iterate over columns with lastName and zipCode
                for col in range(0,2):
                    if worksheet.cell(row,col).value != '':
                        if col == 0:
                            lastName = worksheet.cell(row,col).value
                            listLastName.append(lastName)
                        elif col == 1:
                            zipCode = str(int(worksheet.cell(row,col).value))
                            listZipCode.append(zipCode)
            try:
                workbook = xlwt.Workbook()

                worksheet = workbook.add_sheet('Sheet1')

                #List of items to include the output spreadsheet
                headerItems = ['FirstName','MiddleName','LastName','Gender','AgeRange','FoundAtStreetLine1','FoundAtStreetLine2','FoundAtCity','FoundAtState', \
                'FoundAtZipCode','FoundLatitude','FoundAtLongitude','FoundAtAccuracy','Phones','CurrentAddresses','HistoricalAddresses','AssociatedPeople']

                #Initialize row variable
                x=0

                #Write header row using list of header items
                for i in range(0,len(headerItems)):
                    worksheet.write(0,i, label=headerItems[i])

                #Increment row variable after writing header row
                x+=1

                try:
                    workbook.save(root.outputFileName)
                except IOError:
                    self.textOutputWindow.config(state=NORMAL)
                    self.textOutputWindow.insert(END,'ERROR:  Make sure the output file %s is not already open.\n' %(root.outputFileName))
                    self.textOutputWindow.config(state=DISABLED)
                    #Enable search button since done searching
                    self.buttonExecute.config(state=NORMAL)
                    return

                for name in listLastName:
                    for code in listZipCode:
                        recordsWritten=0

                        if type(name) is not unicode or type(code) is not str:
                            self.textOutputWindow.config(state=NORMAL)
                            self.textOutputWindow.insert (END, "The type for name is %s" %(type(name)))
                            self.textOutputWindow.insert (END, "The type for zipcode is %s" %(type(code)))
                            self.textOutputWindow.config(state=DISABLED)
                            return

                        #Format http request for whitepages api using name, zipcode, and the api key
                        url =  "https://proapi.whitepages.com/3.0/person?name=%s&address.postal_code=%s&api_key=%s" %(name,code,api_key)

                        self.textOutputWindow.config(state=NORMAL)
                        self.textOutputWindow.insert(END,'Sending person request with %s and %s...' %(name,code)+"\n")
                        self.textOutputWindow.config(state=DISABLED)

                        #create response object from https request
                        response = urllib2.urlopen(url)

                        #convert json objects to python objects from response string and store personData
                        personData = json.loads(response.read())

                        self.textOutputWindow.config(state=NORMAL)
                        self.textOutputWindow.insert(END,'Parsing json...\n')
                        self.textOutputWindow.config(state=DISABLED)

                        #Iterate through json elements
                        for person in personData['person']:

                            #Initialize column variable and personRow list for output spreadsheet
                            y=0
                            personRow=[]

                            personRow.append(person['firstname'])

                            personRow.append(person['middlename'])

                            personRow.append(person['lastname'])

                            personRow.append(person['gender'])

                            personRow.append(person['age_range'])

                            personRow.append(person['found_at_address']['street_line_1'])

                            personRow.append(person['found_at_address']['street_line_2'])

                            personRow.append(person['found_at_address']['city'])

                            personRow.append(person['found_at_address']['state_code'])

                            personRow.append(person['found_at_address']['postal_code'])

                            personRow.append(person['found_at_address']['lat_long']['latitude'])

                            personRow.append(person['found_at_address']['lat_long']['longitude'])

                            personRow.append(person['found_at_address']['lat_long']['accuracy'])

                            #Create phones json string for people with at least one phone number
                            if len(person['phones']) > 0:

                                phonesJson='{"phones":['


                                for phone in person['phones']:
                                    #phoneNumber = person['phones']#['[phone_number']
                                    phoneNumber = phone['phone_number']
                                    phoneType = phone['line_type']

                                    phonesJson+='{"phone_number":"%s","line_type":"%s"},' %(phoneNumber,phoneType)

                                #Trim off extra comma
                                if phonesJson[-1] == ",":
                                    phonesJson=phonesJson[0:len(phonesJson)-1]

                                phonesJson+=']}'

                                personRow.append(phonesJson)
                            else:
                                personRow.append(None)

                            #Create current addresses json string for people with at least one current address
                            if len(person['current_addresses']) > 0:

                                currentAddressesJson='{"current_addresses":['

                                for address in person['current_addresses']:

                                    latlong='{"latitude":%s,"longitude":%s,"accuracy":"%s"}' %(address['lat_long']['latitude'],address['lat_long']['longitude'],address['lat_long']['accuracy'])

                                    if address['street_line_2'] is None:
                                        streetline2=''
                                    else:
                                        streetline2=address['street_line_2']

                                    currentAddressesJson+='{"street_line_1":"%s","street_line_2":"%s","city":"%s","postal_code":"%s","zip4":"%s","state_code":"%s","lat_long":%s}'\
                                    %(address['street_line_1'],streetline2,address['city'],address['postal_code'],address['zip4'],address['state_code'],latlong)

                                currentAddressesJson+=']}'

                                personRow.append(currentAddressesJson)
                            else:
                                personRow.append(None)

                            #Create historical addresses json string for people with at least one historical address
                            if len(person['historical_addresses']) > 0:

                                historicalAddressesJson='{"historical_addresses":['

                                for address in person['historical_addresses']:

                                    latlong='{"latitude":%s,"longitude":%s,"accuracy":"%s"}' %(address['lat_long']['latitude'],address['lat_long']['longitude'],address['lat_long']['accuracy'])

                                    if address['street_line_2'] is None:
                                        streetline2=''
                                    else:
                                        streetline2=address['street_line_2']

                                    historicalAddressesJson+='{"street_line_1":"%s","street_line_2":"%s","city":"%s","postal_code":"%s","zip4":"%s","state_code":"%s","lat_long":%s}'\
                                    %(address['street_line_1'],streetline2,address['city'],address['postal_code'],address['zip4'],address['state_code'],latlong)

                                historicalAddressesJson+=']}'

                                personRow.append(historicalAddressesJson)
                            else:
                                personRow.append(None)

                            #Create associated people json string for those with at least one associated person
                            if len(person['associated_people']) > 0:

                                associatedPeopleJson='{"associated_people":['

                                for people in person['associated_people']:

                                    if people['relation'] is None:
                                        relation=''
                                    else:
                                        relation=people['relation']

                                    if people['middlename'] is None:
                                        middlename=''
                                    else:
                                        middlename=people['middlename']

                                    associatedPeopleJson+='{"firstname":"%s","middlename":"%s","lastname":"%s","relation":"%s"}' %(people['firstname'],middlename,people['lastname'],relation)

                                associatedPeopleJson+=']}'

                                personRow.append(associatedPeopleJson)
                            else:
                                personRow.append(None)

                            #Write items from personRow to spreadsheet
                            for item in personRow:
                                worksheet.write(x,y, item)
                                #Increment column variable
                                y+=1

                            #Increment row variable
                            x+=1

                            recordsWritten+=1

                        personCount = personData['count_person']

                        #Save current state of output spreadsheet
                        #workbook.save('PeopleOutput.xls')

                        #print "PersonCount: %s" %(personCount)
                        self.textOutputWindow.config(state=NORMAL)
                        self.textOutputWindow.insert(END,'%d person and associated people included in json response' %(personCount)+'\n')
                        self.textOutputWindow.insert(END,'%d records written to %s' %(recordsWritten,root.outputFileName)+'\n')
                        self.textOutputWindow.config(state=DISABLED)

                        errors = personData['error']
                        warnings = personData['warnings']
            finally:

                #Save current state of spreadsheet
                workbook.save(root.outputFileName)

                #Enable search button since done searching
                self.buttonExecute.config(state=NORMAL)

            #print "Done with input file"
            self.textOutputWindow.config(state=NORMAL)
            self.textOutputWindow.insert(END,'Done with input file')
            self.textOutputWindow.config(state=DISABLED)

        t = threading.Thread(target=worker_thread)
        t.start()
##        except:
##            #Capture exception info to display to user
##            tb = sys.exc_info()[2]
##            tbinfo = traceback.format_tb(tb)[0]
##            pymsg = "EXCEPTION OCCURRED:\nTraceback info\n" + tbinfo + "\nError Info:\n" + str(sys.exc_type) + ":" + str(sys.exc_value) + "\n"
##
##            self.textOutputWindow.config(state=NORMAL)
##            self.textOutputWindow.insert(END,pymsg)
##            self.textOutputWindow.config(state=DISABLED)


#Create GUI using tk and set title and window size

root = Tk()
root.title("People Search")
root.geometry("680x350")

#Start GUI
app = GUI(root)
root.mainloop()











