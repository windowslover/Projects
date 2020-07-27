#-------------------------------------------------------------------------------
# Name:        SplitLineFunction
# Purpose:     Split a line into segments of a specified distance
#
# Author:      Jason Bartling
#
# Created:     19/10/2018
# Copyright:   (c) Jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def split_line(workspacePath, tempGDB, inputFlsplit, splitDistance):
    import arcpy
    import os


    arcpy.env.workspace = workspacePath
    includeEndPoints = 'NO_END_POINTS'

    arcpy.env.overwriteOutput = True

    #mxd = arcpy.mp.ArcGISProject('CURRENT')
    #df = arcpy.mapping.ListDataFrames()[0]

    #Generate points along line for split
    arcpy.SetProgressorLabel("Generating points to split by...")
    outputPointFC = os.path.join(tempGDB,inputFlsplit+"Points")
    arcpy.GeneratePointsAlongLines_management(inputFlsplit, outputPointFC, 'DISTANCE', splitDistance,Include_End_Points = includeEndPoints)

    #Split line into separate segments based on previous points with a 2 meter radius tolerance around the point
    arcpy.SetProgressorLabel("Splitting initial line into segments...")
    outputFCsplit = os.path.join(tempGDB,inputFlsplit+"Split")
    arcpy.SplitLineAtPoint_management(inputFlsplit,outputPointFC, outputFCsplit, search_radius = '1 Meters')

    # Get filename part of outputFCsplit
    flName = os.path.basename(outputFCsplit)

    #Create a feature layer to be used for AddGeometryAttributes
    arcpy.MakeFeatureLayer_management(outputFCsplit,flName)

    #Create a layer object from the feature layer
    #tempLayer = arcpy.mapping.Layer(flName)

    #Add attributes for line start,mid, and end to determine order of segments for new feature classes; for some reason line segments are not in proper order
    arcpy.AddGeometryAttributes_management(flName,"LINE_START_MID_END")

    #Add layer to the map
    #arcpy.mapping.AddLayer(df,tempLayer)

    return outputFCsplit





