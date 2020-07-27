#-------------------------------------------------------------------------------
# Name:        JensenTransects
# Purpose:     Generate transects and points along them for a river centerline
#
# Author:      Jason Bartling
#
#
# Comments: 10/19/2018 Added generate points to segment loop; Processing is taking a really long time for a 20 mile transects section
#
#
# Created:     16/10/2018
# Copyright:   (c) Jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
    #import logic for splitting line into multiple parts based on distance from scripts directory
    from SplitLineFunctionOutsideArcmap import split_line

    #import logic for line transects
    from TransectFunction import generate_transects

    import os
    import arcpy
    import time

    start_time = time.clock()
    print "Script started at {}".format(start_time)

    #arcpy.env.workspace =  arcpy.GetParameterAsText(0)
    arcpy.env.workspace = "C:\Users\jason\Documents\ArcMapStuff\TrinityRiver\Trinity_River.gdb"

    #Save a copy of the workspace to switch back to after temporary processing is done
    permWorkspace = arcpy.env.workspace

    #tempWorkspacePath = arcpy.GetParameterAsText(1)
    tempWorkspacePath = os.path.split(permWorkspace)[0]

    #inputFLsplit = arcpy.GetParameterAsText(2)
    inputFLsplit =  "C:\Users\jason\Documents\ArcMapStuff\TrinityRiver\Trinity_River.gdb\TrinityRiverCenterline"

    #splitDistance = arcpy.GetParameterAsText(3)
    splitDistance = "2 miles"

    #generatePoints = arcpy.GetParameterAsText(4)
    generatePoints = "false"

    tempGDB = os.path.join(tempWorkspacePath,"TEMP.gdb")
    if (arcpy.Exists(tempGDB) == False):
        arcpy.CreateFileGDB_management(tempWorkspacePath, "TEMP", "CURRENT")


    print  "Creating directories..."

    #Set folder variables for output based on workspace directory; for .gdb go back one level
    if permWorkspace.endswith(".gdb"):
        riverSegmentsGDB=os.path.join(os.path.split(permWorkspace)[0],"RIVER_SEGMENTS")

        if os.path.isdir(riverSegmentsGDB) == False:
            #arcpy.CreateFileGDB_management(os.path.split(permWorkspace)[0],"RIVER_SEGMENTS","CURRENT")
            os.mkdir(os.path.join((os.path.split(permWorkspace)[0]),"RIVER_SEGMENTS"))

        transectLinesGDB=os.path.join(os.path.split(permWorkspace)[0],"TRANSECT_LINES")

        if os.path.isdir(transectLinesGDB) == False:
            #arcpy.CreateFileGDB_management(os.path.split(permWorkspace)[0],"TRANSECT_LINES","CURRENT")
            os.mkdir(os.path.join((os.path.split(permWorkspace)[0]),"TRANSECT_LINES"))

        transectPointsGDB=os.path.join(os.path.split(permWorkspace)[0],"TRANSECT_POINTS")

        if os.path.isdir(transectPointsGDB) == False:
            #arcpy.CreateFileGDB_management(os.path.split(permWorkspace)[0],"TRANSECT_POINTS","CURRENT")
            os.mkdir(os.path.join((os.path.split(permWorkspace)[0]),"TRANSECT_POINTS"))
    else:
        riverSegmentsGDB=os.path.join(permWorkspace,"RIVER_SEGMENTS")

        if os.path.isdir(riverSegmentsGDB) == False:
            os.mkdir(os.path.join(permWorkspace,"RIVER_SEGMENTS"))

        transectLinesGDB=os.path.join(permWorkspace,"TRANSECT_LINES")

        if os.path.isdir(transectLinesGDB) == False:
            os.mkdir(os.path.join(permWorkspace,"TRANSECT_LINES"))

        transectPointsGDB=os.path.join(permWorkspace,"TRANSECT_POINTS")

        if os.path.isdir(transectPointsGDB) == False:
            os.mkdir(os.path.join(permWorkspace,"TRANSECT_POINTS"))


    #run split line function
    print "Beginning split line..."
    split_line(permWorkspace,tempGDB, inputFLsplit, splitDistance)

    #redefine outputFCsplit and flName to be used that were created in split_line
    outputFCsplit = os.path.join(tempGDB,inputFLsplit+"Split")
    flName = os.path.basename(outputFCsplit)

    #Create searh cursor from split feature class with object id and start and end points of the line segment
    fields = ['START_X','START_Y','END_X', 'END_Y','OBJECTID']

    #Set workspace to temporary gdb to be removed at end of processing
    searchCursor = arcpy.da.SearchCursor(outputFCsplit, fields)

    segment_list=[]


    # Add all start and end points with shape token for line segments to a list
    for row in searchCursor:
      segment_list.append([[row[0],row[1]],[row[2],row[3]],row[4]])

    del searchCursor

    #Arrange line segments in proper order
    #arcpy.SetProgressorLabel("Ordering line segments...")
    print  "Ordering line segments..."
    segment_list.sort()

    #initialize loop variables
    i=1
    zeroPrefix=""

    #Create new feature class from each segment
    for segment in segment_list:

        segmentNumber=str(i)

        if i < 10:
            zeroPrefix="0"
        else:
            zeroPrefix=""

        segmentNumber=zeroPrefix+segmentNumber
        segmentName=flName+"_segment_"+segmentNumber

        arcpy.SelectLayerByAttribute_management(flName,'NEW_SELECTION',"OBJECTID = "+str(segment[2]))

        #Copy each line segment as a feature class to the temporary geodatabase
        #arcpy.CopyFeatures_management(flName,os.path.join(tempGDB,segmentName))
        arcpy.CopyFeatures_management(flName,os.path.join(riverSegmentsGDB,segmentName))

        #Create a feature layer to be used by transects
        #arcpy.MakeFeatureLayer_management(os.path.join(tempGDB,segmentName),segmentName)
        arcpy.MakeFeatureLayer_management(os.path.join(riverSegmentsGDB,segmentName+".shp"),segmentName+".shp")

        #Add transect FC name to the path for our workspace
        #outputTransectFC = os.path.join(arcpy.env.workspace,segmentName+"Transects")

        #Add full output path to transectLines FC
        outputTransectFC = os.path.join(transectLinesGDB,flName+"_transect_"+segmentNumber)

        #Store transect fc name to be used for points full path
        outputTransectFCname= os.path.split(outputTransectFC)[1]

        #Create path for transect tool to work in; base directory so as not to interfere with current geodatabase
        transectWorkspace = os.path.split(arcpy.env.workspace)[0]

        totalSegments = zeroPrefix+str(len(segment_list))

        #arcpy.SetProgressorLabel("Generating transects for segment {0} of {1}".format(segmentNumber,totalSegments)+"...")
        print "Generating transects for segment {0} of {1}...".format(segmentNumber,totalSegments)
        generate_transects(transectWorkspace,segmentName+".shp","Split at approximate distance", 3, 200, "Meters", outputTransectFC+".shp")

        #Switch back to permanent workspace from temp workspace in transects
        arcpy.env.workspace = permWorkspace

        #Add full output path to transectPoints FC
        outputPointFC = os.path.join(transectPointsGDB,outputTransectFCname+"_points")

        #Only generate points on the transects when the checkbox is selected; ** GREATLY INCREASES PROCESSING TIME **

        if i == 1:

            if generatePoints == 'true':

                #arcpy.SetProgressorLabel("Generating points on transect {0} of {1}".format(segmentNumber,totalSegments)+"...")
                print  "Generating points on transect {0} of {1}...".format(segmentNumber,totalSegments)
                print "OutputTransectFC: {} OutputPointFC: {}".format(outputTransectFC, outputPointFC)
                #arcpy.GeneratePointsAlongLines_management(outputTransectFC, outputPointFC, 'DISTANCE', Distance = '1 meters',Include_End_Points = 'END_POINTS')
                arcpy.GeneratePointsAlongLines_management(outputTransectFC+".shp", outputPointFC+".shp", 'DISTANCE', Distance = '1 meters',Include_End_Points = 'END_POINTS')

        i+=1

    end_time = (time.clock() - start_time)/60
    print "Script took {} minutes to run".format(time.clock() - start_time)

if __name__ == '__main__':
    main()
