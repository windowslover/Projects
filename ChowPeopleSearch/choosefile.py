#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Jason
#
# Created:     18/08/2018
# Copyright:   (c) Jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------


from Tkinter import *   #tkinter gui
import tkFileDialog #file dialog box for input file
import xlrd   #read and write excel spreadsheets
import json   #parse json
import urllib2  #send http request
from WhitePagesAPIKey import api_key   #api key for people search request

class Application(Frame):

    def __init__(self, master):
        Frame.__init__(self,master)
        self.grid()
        self.create_widgets()
        root.filename = None
        root.count = 0

    def create_widgets(self):

        self.buttonFileChooser = Button(self, text = "Choose File")
        self.buttonFileChooser["command"] = self.select_file
        self.buttonFileChooser.grid(row = 0, column = 0, padx = 5, pady = 5)

        self.textFilePath = Text(self, width = 60, height = 1)
        self.textFilePath.grid(row = 0, column = 1)

        self.buttonExecute = Button(self, text = "Search")
        self.buttonExecute["command"] = self.people_search
        self.buttonExecute.grid(row = 1, column = 0, padx = 20, pady = 10 )

        self.textOutputWindow = Text(self, width = 60, height = 14)
        self.textOutputWindow.grid(row = 1, column = 1)
        self.scrollBar = Scrollbar(self, orient=VERTICAL, command=self.textOutputWindow.yview)

        #Use sticky property with N(orth) and S(outh) to allow scrollbar to scretch to fit next to the output window
        self.scrollBar.grid(row =1, column = 2, sticky=(N,S), padx=5)
        self.textOutputWindow.configure(yscrollcommand=self.scrollBar.set)
        #Create as read only just for display purposes
        self.textOutputWindow.config(state=DISABLED)

    def people_search(self):

        #Clear OutputWindow text
        self.textOutputWindow.delete(1.0, END)

        #Check that input file has actually been selected to process
        if  root.filename is None:
            self.textOutputWindow.config(state=NORMAL)
            self.textOutputWindow.insert (END, "No input file selected")
            self.textOutputWindow.config(state=DISABLED)
        else:
            workbook = xlrd.open_workbook(root.filename)
            worksheet = workbook.sheet_by_index(0)

            listLastName = []
            listZipCode = []

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

                    #print "Sending person request with %s and %s..." %(name, code)
                    self.textOutputWindow.config(state=NORMAL)
                    self.textOutputWindow.insert(END,'Sending person request with %s and %s...' %(name,code)+"\n")
                    self.textOutputWindow.config(state=DISABLED)

                    url =  "https://proapi.whitepages.com/3.0/person?name=%s&address.postal_code=%s&api_key=%s" %(name,code,api_key)

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

            print "Done with input file"


    #Select input file for people search and display path in textbox
    def select_file(self):
        root.filename = tkFileDialog.askopenfilename(initialdir = "/", title = "Select File")

        self.textFilePath.insert (0.0, root.filename)

        #Get the value of the textbox from line 1 character zero to the end of the textbox minus one character for newline
        #print self.textFilePath.get("1.0", 'end-1c')

root = Tk()
root.title("People Search")
root.geometry("650x300")

app = Application(root)
root.mainloop()






