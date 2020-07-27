#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Jason
#
# Created:     15/03/2018
# Copyright:   (c) Jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# *** Problems and workarounds with places: ***
# Problem:  It is not possible at this time to get the detailed place description (discriminate between real golf and mini golf)
# Problem:  Not able to get number of reviews to determine overall review accuracy  Solution:  Get top reviews that are less than 5 to filter out 1 5 star reviews only
def main():
    #Text Search https://maps.googleapis.com/maps/api/place/textsearch/xml?query=miniature+golf+in+texas&key=api_key
    #Place Details https://maps.googleapis.com/maps/api/place/details/xml?placeid=ChIJl5TEAAdrsocRoh1Jub5u-AY&key=api_key
    #Add &pagetoken for next pages
    import arcpy
    import urllib2
    import time
    import xml.etree.ElementTree as ET
    from GoogleAPIkey import api_key

    #Build url request using search text, access token, and next_page_token
    def build_URL(search_text, ACCESS_TOKEN,next_page_token= ''):
        base_url = 'https://maps.googleapis.com/maps/api/place/textsearch/xml'     # Can change json to xml to change output type
        key_string = '&key='+ACCESS_TOKEN                                           # First think after the base_url starts with ? instead of &
        query_string = '?query='+urllib2.quote(search_text)
        page_token = '&pagetoken='+next_page_token

        if next_page_token != '':
            url = base_url+query_string+key_string+page_token
        else:
            url = base_url+query_string+key_string

        return url

    region = arcpy.GetParameterAsText(2) #script tool parameter

    if region == 'CentralSouthwest':
        statesList = {'Arkansas','Iowa','Louisiana','Missouri','Texas','Nebraska','New Mexico','Oklahoma','Colorado','Kansas'}
    elif region == 'Northeast':
        statesList = {'Connecticut','Maine','Massachusetts','New Hampshire','Rhode Island','Vermont','New Jersey','New York','Pennsylvania'}
    elif region == 'Midwest':
        statesList = {'Illinois','Wisconsin','Michigan','Ohio','Indiana','North Dakota','South Dakota','Nebraska','Kansas','Minnesota',
        'Iowa','Missouri'}
    elif region == 'West':
        statesList = {'Arizona','New Mexico','Colorado','Utah','Wyoming','Montana','Idaho','Nevada','Washington','Oregon','California'}
    elif region == 'Southeast':
        statesList = {'Mississippi','Alabama','Georgia','Florida','South Carolina','North Carolina','Tennessee','Kentucky','Virginia','West Virginia',
        'Maryland','Delaware'}
    elif region == 'TexasAdjacent':
        statesList = {'Texas','Oklahoma','Arkansas','Louisiana'}
    else:
        statesList = ['Washington','Oregon','California','Idaho','Nevada','Arizona','Utah','New Mexico','Colorado','Wyoming',
    'Montana','North Dakota','South Dakota','Nebraska','Kansas','Oklahoma','Texas','Louisiana','Arkansas','Missouri',
    'Iowa','Minnesota','Wisconsin','Illinois','Indiana','Michigan','Ohio','Kentucky','Tennessee','Mississippi',
    'Alabama','Florida','Georgia','South Carolina','North Carolina','Virginia','West Virginia','Maryland','Delaware','New Jersey',
    'Pennsylvania','New York','Connecticut','Rhode Island','Massachusetts','Vermont','New Hampshire','Maine']


    #statesList.sort()

    workspacePath = arcpy.GetParameterAsText(0) #script tool parameter
    arcpy.env.workspace = workspacePath

    #Location to search for
    searchTerm = arcpy.GetParameterAsText(1) #script tool parameter
    #searchTerm = 'mini golf'

    #Remove spaces from searchTerm and rejoin them with proper capitilization
    file_prefix = ''
    for words in searchTerm.split():
        file_prefix += words.capitalize()

    #file_path = r'H:\GEO 4393C\FinalProject\Project.gdb\MiniGolfLocations.csv'
    file_path = workspacePath+'\\'+file_prefix+'Locations.csv'
    out_file = open(file_path,'w')
    out_file.write('NAME,ADDRESS,LATITUDE,LONGITUDE,RATING\n')

    i = 0

    for state in statesList:

        #search_text='Miniature Golf Course in '+state
        search_text= searchTerm + ' in ' + state

        url = build_URL(search_text,api_key)


        response = urllib2.urlopen(url)
        #print response.read()
        connection_closed = False

        root = ET.fromstring(response.read())

        status = root.find('status').text

        if status == 'OK':
            next_page = root.find('next_page_token')

            #Set next_page token to initial default state if no next page is found for first result set
            next_page_token = ''

            while next_page_token != 'NONE':

                #Open another connection to google places api for subsequent page tokens
                if connection_closed:
                    #Sleep so that next page of results can be generated
                    time.sleep(1.5)

                    url = build_URL(search_text, api_key,next_page_token)

                    response = urllib2.urlopen(url)
                    root = ET.fromstring(response.read())

                #loop through all result tags
                for result in root.findall('result'):
                    i += 1

                    #Create OID field
                    oid = str(i)

                    #find relevant child tags to get values
                    name_text = result.find('name').text
                    address_text = result.find('formatted_address').text
                    geometry = result.find('geometry')
                    location = geometry.find('location')
                    latitude_text = location.find('lat').text
                    longitude_text = location.find('lng').text
                    rating = result.find('rating')

                    if rating is not None:
                        rating_text = rating.text
                    else:
                        rating_text = 'NONE'

                    #Replace any errant ascii text and ensure unicode
                    try:
                        name_text = name_text.encode('utf8')
                        address_text = address_text.encode('utf8')


                    except TypeError:
                        print 'Encountered type error for %s with address_text %s' %(state,address_text)

                    out_file.write('"'+name_text+'",'+'"'+address_text+'",'+latitude_text+','+longitude_text+','+rating_text+'\n')


                #For the last page of results set next page token to none
                if root.find('next_page_token') is None:
                    next_page_token = 'NONE'
                else:
                    next_page_token = root.find('next_page_token').text


                response.close()
                connection_closed = True

            print 'Done with %s' %(state)
        else:
            error = root.find('error_message')

            #print an error message if there is one otherwise just the error code
            if error is not None:
                error_message = error.text
                arcpy.AddError('ERROR: The search in {2} was not completed.  Response: {0} Error: {1}'.format(status,error_message,state))
            else:
                arcpy.AddError('ERROR: The search in {1} was not completed.  Response: {0}'.format(status,state))

            response.close()
            #out_file.close()
            #exit()

    #print '%d results were saved to %s' %(i, file_path)
    arcpy.AddMessage('{0} results were saved to {1}'.format(i, file_path))
    out_file.close()

if __name__ == '__main__':
    main()
