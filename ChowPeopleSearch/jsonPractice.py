#-------------------------------------------------------------------------------
# Name:        WhitePages Demo Download
# Purpose:     Download demographic data for certain surname and zip code combinations
#
#Input:        File with surnames in one column and  zip codes in another
#Output:       Demographic data to store in database
# Author:      jason
#
# Created:     14/08/2018
# Copyright:   (c) jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
    import json
    import urllib2
    from WhitePagesAPIKey import api_key
    import xlwt #Write to an excel spreadsheet

    def download_json():
        print "Downloading json \n"
        #url = "https://jsonplaceholder.typicode.com/todos"
        name = "Huynh"
        zipCode = "77001"
        #url = "https://proapi.whitepages.com/3.0/person?name=Jason+Bartling&address.city=San+Marcos&address.state_code=TX&api_key="+api_key
        url =  "https://proapi.whitepages.com/3.0/person?name=%s&address.postal_code=%s&api_key=%s" %(name,zipCode,api_key)

        #create response object from https request
        response = urllib2.urlopen(url)

        #convert json objects to python objects from response string and store personData
        personData = json.loads(response.read())

        #open output file and format as json with personData
        outfile = open("sample.json","w")
        json.dump(personData,outfile, indent=2)

    def read_json():
        print "Reading json \n"
        infile = open("sample.json","r")

        personData = json.load(infile)

        #print personData
        try:
            workbook = xlwt.Workbook()

            worksheet = workbook.add_sheet('Sheet1')

            #List of items to include the output file
            headerItems = ['FirstName','MiddleName','LastName','Gender','AgeRange','FoundAtStreetLine1','FoundAtStreetLine2','FoundAtCity','FoundAtState', \
            'FoundAtZipCode','FoundLatitude','FoundAtLongitude','FoundAtAccuracy','Phones','CurrentAddresses','HistoricalAddresses','AssociatedPeople']

            #Initialize row variable
            x=0

            #Write header row using list of header items
            for i in range(0,len(headerItems)):
                worksheet.write(0,i, label=headerItems[i])

            #Increment row variable after writing header row
            x+=1


            for person in personData['person']:

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


            workbook.save('PeopleOutput.xls')



        #except:
            #print 'Exception occurred row: {0} column: {1} item: {2}'.format(x,y,blah)
            #pass

        finally:
            workbook.save('PeopleOutput.xls')
            print 'Done creating spreadsheet'
                #print phonesJson

##                blah=json.loads(phonesJson)
##
##                print blah
##
##                i=1
##
##                for phone in blah:
##                    print 'PhoneRecord%d: %s %s' %(i,phone['phone_number'],phone['line_type'])
##                    i+=1








        personCount = personData['count_person']

        #print "PersonCount: %s" %(personCount)
        errors = personData['error']
        warnings = personData['warnings']


    #download_json()

    read_json()

if __name__ == '__main__':
    main()
