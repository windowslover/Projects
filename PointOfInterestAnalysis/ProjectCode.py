#-------------------------------------------------------------------------------
# Name:        Point of Interest Locations Analysis
# Purpose:   Calculate nearest neighbor distance and filter locations by rating to observe overall quality and clustering in a given region
#
# Author:      Jason Bartling
#
# Created:     20/03/2018
# Copyright:   (c) j_b372 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
    import arcpy
    import os
    import sys
    import traceback
    import timeit

    #Set environment
    #basePath = 'C:\Users\Jason\Documents\SchoolStuff\GEO 4393C'
    #workspacePath = basePath+'\FinalProject\Project.gdb'
    workspacePath = arcpy.GetParameterAsText(0)  #script tool parameter
    arcpy.env.workspace = workspacePath
    arcpy.env.overwriteOutput = True

    #Global variables
    statesOutline = arcpy.GetParameterAsText(1)  #script tool parameter
    #statesOutline = basePath+'\FinalProject\Project.gdb\states_gen'
    locationsFilePath = arcpy.GetParameterAsText(2) #script tool parameter
    #locationsFilePath = basePath+'\FinalProject\Locations\MiniGolfLocations.csv'
    #mxd = arcpy.mapping.MapDocument('FinalProject.mxd')
    mxd = arcpy.mapping.MapDocument('CURRENT')
    df = arcpy.mapping.ListDataFrames(mxd)[0]
    #minRating = '3.5'
    minRating = arcpy.GetParameterAsText(3)  #script tool parameter

    #Set default value for minimum rating is none is selected
    if minRating == '':
        minRating = '0'

    #Set spatial reference for projecting data
    srName = "USA Contiguous Equidistant Conic"
    sr = arcpy.SpatialReference(srName)

    region = arcpy.GetParameterAsText(4) #script tool parameter

    #Base preset region on user input
    if region == 'CentralSouthwest':
        statesDict = {'Arkansas':'AR','Iowa':'IA','Louisiana':'LA','Missouri':'MO','Texas':'TX','Nebraska':'NE','New Mexico':'NM','Oklahoma':'OK','Colorado':'CO','Kansas':'KS'}
    elif region == 'Northeast':
        statesDict = {'Connecticut':'CT','Maine':'ME','Massachusetts':'MA','New Hampshire':'NH','Rhode Island':'RI','Vermont':'VT','New Jersey':'NJ','New York':'NY','Pennsylvania':'PA'}
    elif region == 'Midwest':
        statesDict = {'Illinois':'IL','Wisconsin':'WI','Michigan':'MI','Ohio':'OH','Indiana':'IN','North Dakota':'ND','South Dakota':'SD','Nebraska':'NE','Kansas':'KS','Minnesota':'MN',
        'Iowa':'IA','Missouri':'MO'}
    elif region == 'West':
        statesDict = {'Arizona':'AZ','New Mexico':'NM','Colorado':'CO','Utah':'UT','Wyoming':'WY','Montana':'MT','Idaho':'ID','Nevada':'NV','Washington':'WA','Oregon':'OR','California':'CA'}
    elif region == 'Southeast':
        statesDict = {'Mississippi':'MS','Alabama':'AL','Georgia':'GA','Florida':'FL','South Carolina':'SC','North Carolina':'NC','Tennessee':'TN','Kentucky':'KY','Virginia':'VA','West Virginia':'WV',
        'Maryland':'MD','Delaware':'DE'}
    elif region == 'TexasAdjacent':
        statesDict = {'Texas':'TX','Oklahoma':'OK','Arkansas':'AR','Louisiana':'LA'}

    else:
        statesDict = {'Washington':'WA','Oregon':'OR','California':'CA','Idaho':'ID','Nevada':'NV','Arizona':'AZ','Utah':'UT','New Mexico':'NM','Colorado':'CO','Wyoming':'WY',
        'Montana':'MT','North Dakota':'ND','South Dakota':'SD','Nebraska':'NE','Kansas':'KS','Oklahoma':'OK','Texas':'TX','Louisiana':'LA','Arkansas':'AR','Missouri':'MO',
        'Iowa':'IA','Minnesota':'MN','Wisconsin':'WI','Illinois':'IL','Indiana':'IN','Michigan':'MI','Ohio':'OH','Kentucky':'KY','Tennessee':'TN','Mississippi':'MS',
        'Alabama':'AL','Florida':'FL','Georgia':'GA','South Carolina':'SC','North Carolina':'NC','Virginia':'VA','West Virginia':'WV','Maryland':'MD','Delaware':'DE','New Jersey':'NJ',
        'Pennsylvania':'PA','New York':'NY','Connecticut':'CT','Rhode Island':'RI','Massachusetts':'MA','Vermont':'VT','New Hampshire':'NH','Maine':'ME'}

    # Create a new mxd to work with
    def CreateMXD(newMxd):

        #Locate install directory for arcgis
        installDir = arcpy.GetInstallInfo()['InstallDir']

        #Set map template file location
        templateDir = os.path.join(installDir,'MapTemplates','Standard Page Sizes','North American (ANSI) Page Sizes')
        mapTemplate = templateDir+r'\ANSI C Portrait.mxd'

        # Save a copy of the chosen template as a new map document
        mxd = arcpy.mapping.MapDocument(mapTemplate)
        mxd.saveACopy(newMxd)

        print 'New map document saved to %s' %(newMxd)

        del mxd

    #Add states to map based on defined region
    def ClipStates(mxd, sr, statesList,statesOutline):

        #mxd = arcpy.mapping.MapDocument(newMxd)
        #df = arcpy.mapping.ListDataFrames(mxd)[0]
        df.spatialReference = sr
        print "Changed spatial reference for data frame"

        #Project states to intended coordinate system
        #arcpy.Project_management('states_gen','states_proj',sr)
        arcpy.Project_management(statesOutline,'states_proj',sr)
        print 'Projected states to %s' %(srName)

        # Create layer from states shape file
        arcpy.MakeFeatureLayer_management('states_proj','states')

        #Make a subselection if statesList is not the full contigous US
        if len(statesList) < 48:
            #Select states from statesList to clip by
            for state in statesList:
                arcpy.SelectLayerByAttribute_management('states','ADD_TO_SELECTION',"NAME = "+"'"+state+"'")

        #Create feature class of selected states and the temp layer to add to the map
        arcpy.CopyFeatures_management('states','statesSelection')
        arcpy.MakeFeatureLayer_management('statesSelection','states')

        print 'States clipped to selected region'

    #Add top 3 minigolf locations to map for each state and calculate nearest neighbor distance for filtered courses
    def AddLocations(mxd, sr, statesList, locationsFilePath):

        def NearestNeighbor(fc,i,locationType):

            distanceTable = 'nnDistance'

            #Create table for output
            tableExists = arcpy.ListTables(distanceTable)

            #Check for existing table before creating
            if tableExists == []:
                arcpy.CreateTable_management(workspacePath,distanceTable)
                arcpy.AddField_management(distanceTable,'StateName','TEXT')
                arcpy.AddField_management(distanceTable,'NNdistance','FLOAT')

                #Location stats
                arcpy.AddField_management(distanceTable,'LOCATION_COUNT','SHORT')
                arcpy.AddField_management(distanceTable,'LOCATION_DENSITY','FLOAT')

            #Table variables
            fields = ['OBJECTID','StateName','NNdistance']

            #Open cursor to distanceTable for inserting
            cursor = arcpy.da.InsertCursor(distanceTable,fields)

            #Calculate average nearest neighbor stats
            nn_output = arcpy.AverageNearestNeighbor_stats(fc,"EUCLIDEAN_DISTANCE","NO_REPORT")

            #Grab observed distance and convert from meters to miles
            obsDistance = round((float(nn_output[4]) *  0.000621371),2)

            #Add space back to name for those states that should have one (required for joining purposes);  Index of -1 returned for those not found
            if fc.find('New') != -1:
                fc = fc.replace('New','New ')
            elif fc.find('North') != -1:
                fc = fc.replace('North','North ')
            elif fc.find('South') != -1:
                fc = fc.replace('South','South ')
            elif fc.find('West') != -1:
                fc = fc.replace('West','West ')
            elif fc.find('Rhode') != -1:
                fc = fc.replace('Rhode','Rhode ')

            #Remove activity from stateName
            stateName = fc.replace(locationType+'Filtered','')

            #Add values to table
            row = [i,stateName,obsDistance]
            cursor.insertRow(row)
            #i+=1

            del cursor

        # Calculate some summary statistics for our filtered locations using state name and filtered FC
        def LocationStats(key, lsFc):

            stateName = key
            searchCursor = arcpy.da.SearchCursor('statesSelection',['NAME','density'],where_clause = "NAME = '"+stateName+"'")

            for row in searchCursor:
                popDensity = row[1]

                #Get correct feature class based on stateName and count the number of locations
                locationCount = int(arcpy.GetCount_management(lsFc)[0])

                #People per square mile per location;  a lower number means more locations in relation to population density
                locationDensity = round(popDensity/locationCount,2)

                updateCursor = arcpy.da.UpdateCursor('nnDistance',['StateName','LOCATION_COUNT','LOCATION_DENSITY'], where_clause = "StateName = '"+stateName+"'")

                #update state record with filtered locationCount and density
                for row in updateCursor:
                    if row[0] == stateName:
                        row[1] = locationCount
                        row[2] = locationDensity
                        updateCursor.updateRow(row)

            del searchCursor
            del updateCursor

        locationsLyr = 'us_locations'

        #Variables for creating layer names and feature classes
        locationsFile = os.path.basename(locationsFilePath)
        outFileName = locationsFile.replace('.csv','')
        locationType = outFileName.replace('Locations','')

        #Create empty point feature class and add columns
        gcs = arcpy.SpatialReference('NAD 1983')
        arcpy.CreateFeatureclass_management(workspacePath,'USpoints','POINT', spatial_reference = gcs)
        arcpy.AddField_management('USpoints','NAME','TEXT')
        arcpy.AddField_management('USpoints','ADDRESS','TEXT')
        arcpy.AddField_management('USpoints','RATING','TEXT')

        searchCursor = arcpy.da.SearchCursor(locationsFilePath,['NAME','ADDRESS','LATITUDE','LONGITUDE','RATING'])
        insertCursor = arcpy.da.InsertCursor('USpoints',['SHAPE@XY','NAME','ADDRESS','RATING'])

        #Loop through locations file and insert data into USpoints feature class
        for row in searchCursor:
            name = row[0]
            address = row[1]
            latitude = row[2]
            longitude = row[3]
            rating = row[4]

            fields = [[longitude,latitude],name,address,rating]

            insertCursor.insertRow(fields)

        del searchCursor
        del insertCursor

        arcpy.Project_management(os.path.join(workspacePath,'USpoints'),os.path.join(workspacePath,outFileName), sr)
        arcpy.MakeFeatureLayer_management(os.path.join(workspacePath,outFileName),locationsLyr)

        #Iterate through states list to make separate shape files for each state
        for state in statesList:

            #Select state to clip by
            arcpy.MakeFeatureLayer_management('states_proj','statesLyr')
            arcpy.SelectLayerByAttribute_management('statesLyr','NEW_SELECTION',"NAME = "+"'"+state+"'")

            #make a copy of state in key to reuse later to retrieve the state abbrev
            key = state

            #remove any spaces in the state name
            state = state.replace(" ","")
            #fcName = state+'MiniGolf'
            fcName = state+locationType

            newFc = os.path.join(workspacePath,fcName)

            #Clip total locations to individual state
            arcpy.Clip_analysis(locationsLyr,'statesLyr',newFc)

            #Add columns for city and state to table
            arcpy.AddField_management(fcName,"CITY","TEXT")
            arcpy.AddField_management(fcName,"STATE","TEXT")

            #Populate city and state fields based on address text
            updatecursor = arcpy.da.UpdateCursor(fcName,['ADDRESS','CITY','STATE'])
            for row in updatecursor:
                #Find state position in address so we can extract the city using the comma position before and after city
                second_comma = row[0].find(', '+statesList[key])
                first_comma = row[0].rfind(',',0, second_comma - 1)
                city = row[0][first_comma + 2 : second_comma]

                #update city and state field
                row[1] = city
                row[2] = statesList[key]

                updatecursor.updateRow(row)

            del updatecursor

            #Create layer of clipped locations
            arcpy.MakeFeatureLayer_management(newFc,fcName)

            #Select only locations that are above the minimum rating and eliminate courses that aren't vetted
            sql = "RATING >= '"+minRating+"' AND RATING NOT IN ('NONE','5.0')"
            arcpy.SelectLayerByAttribute_management(fcName,'NEW_SELECTION',sql)

            #Remove courses that are likely not to be miniature golf
            sql = "(NAME LIKE '%Golf Club' OR NAME LIKE '%Golf Course%' OR NAME LIKE '%Links%' ) AND NAME NOT LIKE '%Mini%Golf Course'"
            arcpy.SelectLayerByAttribute_management(fcName,'REMOVE_FROM_SELECTION',sql)

            #Remove other locations that were somehow included and aren't mini golf
            sql = "NAME IN ('Gallup Cultural Center','Tower Tee Batting Cages','Ole Chi Mill','Valley Bowl Fun Center')"
            arcpy.SelectLayerByAttribute_management(fcName,'REMOVE_FROM_SELECTION',sql)

            filteredFc = fcName+'Filtered'

            #Save off a copy of the filtered locations by rating
            arcpy.CopyFeatures_management(fcName,os.path.join(workspacePath,filteredFc))

            #try calculating nearest neighbor one at a time before top 3 is created
            j = 1
            NearestNeighbor(filteredFc,j,locationType)
            LocationStats(key, filteredFc)
            j += 1

            #Search for top 3 locations in each state
            sqlClause = (None, 'ORDER BY RATING DESC')
            rows = arcpy.da.SearchCursor (filteredFc,field_names = ['OBJECTID','RATING','ADDRESS'],sql_clause = sqlClause)

            i = 1
            topList = []
            address = ''
            for row in rows:
                if len(topList) < 3:
                    if address != row[2]:
                        topList.append(row[0])
                        address = row[2]
                else:
                    break

            del rows

            arcpy.MakeFeatureLayer_management(os.path.join(workspacePath,filteredFc),filteredFc)

            try:
                arcpy.SelectLayerByAttribute_management(filteredFc,'ADD_TO_SELECTION','OBJECTID = '+str(topList[0]))
                arcpy.SelectLayerByAttribute_management(filteredFc,'ADD_TO_SELECTION','OBJECTID = '+str(topList[1]))
                arcpy.SelectLayerByAttribute_management(filteredFc,'ADD_TO_SELECTION','OBJECTID = '+str(topList[2]))
            # Catch index error and proceed normally; this just means there are less than 3 top locations
            except IndexError:
                pass

            #Save a copy of the top3 and add it to the map
            topLoc = fcName+'Top3'
            arcpy.CopyFeatures_management(filteredFc,topLoc)
            arcpy.MakeFeatureLayer_management(os.path.join(workspacePath,topLoc),topLoc)

            newLayer = arcpy.mapping.Layer(topLoc)

            #Update label expression and turn on labels
            for lblClass in newLayer.labelClasses:
                #VBcode for label exrepssion
                lblClass.expression = '[NAME] & VbCrLf & [CITY] & "," & [STATE] & "," & [RATING]'

            newLayer.showLabels = True

            arcpy.mapping.AddLayer(df, newLayer)

        #Clear variables
        del newLayer

    #Join nnDistance table to states layer and add it to the map
    def AddStates(mxd):


        #Join table to states feature class
        arcpy.JoinField_management('statesSelection','NAME','nnDistance','StateName',['NNdistance','LOCATION_COUNT','LOCATION_DENSITY'])
        print 'Done joining nnDistance to states_selection'

        #Create temp layer for adding
        arcpy.MakeFeatureLayer_management('statesSelection','states')

        #Add the new layer to the map
        newLayer = arcpy.mapping.Layer('states')

        #Update label expression and turn on labels
        for lblClass in newLayer.labelClasses:
            #VBcode for label exrepssion
            lblClass.expression = "[STUSPS]"

        newLayer.showLabels = True

        #Update symbology based on lyrfile
        #lyrFile = arcpy.mapping.Layer(r'H:\GEO 4393C\FinalProject\statesSym.lyr')
        #arcpy.mapping.UpdateLayer(df,newLayer,lyrFile,True)
        #sym = newLayer.symbology
        #sym.updateRenderer('GraduatedColorsRenderer')
        #sym.renderer.classificationField = 'NNdistance'
        #sym.classificationMethod = 'NaturalBreaks'
        #sym.renderer.breakCount = 5




        #Set extent of df to states
        df.zoomToSelectedFeatures()

        arcpy.mapping.AddLayer(df,newLayer)
        print "Added states to map"

    try:
        #time program execution
        start = timeit.default_timer()

        #Execute major operations
        ClipStates(mxd,sr,statesDict,statesOutline)
        AddLocations(mxd,sr,statesDict,locationsFilePath)
        AddStates(mxd)

    #Handle geoprocessing and regular python errors
    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        print "An error has occurred\n"
        pymsg = "PYTHON ERRORS:\nTraceback info\n" + tbinfo + "\nError Info:\n" + str(sys.exc_type) + ":" + str(sys.exc_value) + "\n"
        arcpy.AddError(pymsg)
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(msgs)
        print pymsg + "\n"
        print msgs
    finally:
        stop = timeit.default_timer()
        print 'Program execution time was {0} seconds'.format(round(stop - start),2)

        #Check that user is running off a currently saved mxd, if not save a copy with a new name
        if mxd.filePath == '':
            mxd.saveACopy('..\..\FinalProject\NewMap.mxd')
            arcpy.AddMessage('Map data saved to {0}'.format('..\..\FinalProject\NewMap.mxd'))
        #Save mxd and release the memory lock
        else:
            mxd.save()
        del mxd


if __name__ == '__main__':
    main()
