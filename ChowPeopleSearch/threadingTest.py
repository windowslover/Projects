#-------------------------------------------------------------------------------
# Name:        People Search
# Purpose:     Download demographic data for certain surname and zip code combinations
#
#Input:        File with surnames in one column and  zip codes in another
#              .Xslx (spreadsheet) input file most be formatted with last name in first column and zip code in second column both starting in the second row  (Sample file SmallSample.xslx)
#
#Output:       Demographic data in a .csv file (Outputfile.csv)
#
# Author:      Jason Bartling
#
# Created:     23/08/2018
# Copyright:   (c) Jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------


from Tkinter import *   #tkinter gui
import tkFileDialog #file dialog box for input file
import ttk    #Library for progress bar
import xlrd   #read and write excel spreadsheets
import json   #parse json
import urllib2  #send http request
import sys
from WhitePagesAPIKey import api_key   #api key for people search request
import threading

class GUI(Frame):

    def __init__(self, master):
        Frame.__init__(self,master)
        self.grid()
        self.create_widgets()
        root.filename = None
        root.count = 0
        peoplethread= None

    def create_widgets(self):

        self.buttonFileChooser = Button(self, text = "Choose File")
        self.buttonFileChooser["command"] = self.select_file
        self.buttonFileChooser.grid(row = 0, column = 0, padx = 5, pady = 5)

        self.textFilePath = Text(self, width = 65, height = 1)
        self.textFilePath.grid(row = 0, column = 1)

        self.buttonExecute = Button(self, text = "Search")
        #peoplethread = threading.Thread(target=self.people_search)
        self.buttonExecute["command"] = self.people_search
        #self.buttonExecute["command"] = peoplethread.start
        self.buttonExecute.grid(row = 1, column = 0, padx = 20, pady = 10 )


        self.textOutputWindow = Text(self, width = 65, height = 14)
        self.textOutputWindow.grid(row = 1, column = 1)

        #Tie scrollbar to output window text box
        self.scrollBar = Scrollbar(self, orient=VERTICAL, command=self.textOutputWindow.yview)

        #Use sticky property with N(orth) and S(outh) to allow scrollbar to scretch to fit next to the output window
        self.scrollBar.grid(row =1, column = 2, sticky=(N,S), padx=5)

        #Tie output window text box to scroll bar
        self.textOutputWindow.configure(yscrollcommand=self.scrollBar.set)

        #Create as read only just for display purposes
        self.textOutputWindow.config(state=DISABLED)

        #** Progress bar not working may need to use threading??**
        #self.progressbar = ttk.Progressbar(self, orient=HORIZONTAL, length=490, mode='indeterminate')
        #self.progressbar.grid(row = 2, column = 1, sticky = (W), pady=10)



    #Select input file for people search and display path in textbox
    def select_file(self):
        root.filename = tkFileDialog.askopenfilename(initialdir = "/", title = "Select File")

        self.textFilePath.insert (0.0, root.filename)

        #Get the value of the textbox from line 1 character zero to the end of the textbox minus one character for newline
        #print self.textFilePath.get("1.0", 'end-1c')

    #Function to do the bulk of the people searching called from clicking the search button
    def people_search(self):

        #Create separate function to be handled as a thread so that GUI does not freeze
        def worker_thread():
            #Clear OutputWindow text
            self.textOutputWindow.config(state=NORMAL)
            self.textOutputWindow.delete(1.0, END)

            #Check that input file has actually been selected to process
            if  root.filename is None or root.filename is '':
                self.textOutputWindow.config(state=NORMAL)
                self.textOutputWindow.insert (END, "No input file selected")
                self.textOutputWindow.config(state=DISABLED)
            else:

                #start progress bar progress  ** Progress bar not working may need to use threading??**
                #self.progressbar.start

                #Open workbook and worksheet; Catch error for invalid file type if not excel spreadsheet
                try:
                    workbook = xlrd.open_workbook(root.filename)
                    worksheet = workbook.sheet_by_index(0)
                except xlrd.XLRDError:
                    self.textOutputWindow.config(state=NORMAL)
                    self.textOutputWindow.insert (END, "ERROR:  Make sure input file is a .xls or .xlsx excel file")
                    self.textOutputWindow.config(state=DISABLED)
                    return


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

                #self.textOutputWindow.insert(0.0, lastName)
                outFile = open("Outputfile.csv","w")

                outFile.write("FirstName,MiddleName,LastName,AgeRange,StreetLine1,StreetLin2,City,State,ZipCode,Latitude,Longitude\n") ##May need to add separate columns with phone types and number separated by comma

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

                        for person in personData['person']:

                            firstName = person['firstname']

                            middleName = person['middlename']

                            lastName = person['lastname']

                            ageRange = person['age_range']

                            streetLine1 = person['found_at_address']['street_line_1']

                            streetLine2 = person['found_at_address']['street_line_2']

                            city = person['found_at_address']['city']

                            state = person['found_at_address']['state_code']

                            zipCode = person['found_at_address']['postal_code']

                            latitude = person['found_at_address']['lat_long']['latitude']

                            longitude = person['found_at_address']['lat_long']['longitude']

                            if person['phones'] is not None:

                                for phone in person['phones']:
                                    phoneNumber = phone['phone_number']
                                    phoneType = phone['line_type']
                                    #print 'Phone: %s' %(phoneNumber)
                                    #print 'LineType: %s' %(phoneType)

                            outFile.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' %(firstName,middleName,lastName,ageRange,streetLine1,streetLine2,city,state,zipCode,latitude,longitude))

                            recordsWritten+=1

                        personCount = personData['count_person']

                        #print "PersonCount: %s" %(personCount)
                        self.textOutputWindow.config(state=NORMAL)
                        self.textOutputWindow.insert(END,'%d person and associated people included in json response' %(personCount)+'\n')
                        self.textOutputWindow.insert(END,'%d records written to OutputFile.csv' %(recordsWritten)+'\n')
                        self.textOutputWindow.config(state=DISABLED)

                        errors = personData['error']
                        warnings = personData['warnings']

                outFile.close()

                #print "Done with input file"
                self.textOutputWindow.config(state=NORMAL)
                self.textOutputWindow.insert(END,'Done with input file')
                self.textOutputWindow.config(state=DISABLED)

                #peoplethread.stop()

                #End progress for progressbar to show program has finished
                #self.progressbar.stop

        #Create thread and start it for responsive output in output window textbox
        t = threading.Thread(target=worker_thread)
        t.start()

#Create GUI using tk and set title and window size
root = Tk()
root.title("People Search")
root.geometry("650x350")

#Start GUI
app = GUI(root)
root.mainloop()







