#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Jason
#
# Created:     15/10/2018
# Copyright:   (c) Jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import arcpy
import os

arcpy.env.workspace =  arcpy.GetParameterAsText(0)
inputLineFLpoints = arcpy.GetParameterAsText(1)
outputPointFC = arcpy.GetParameterAsText(2)
splitDistance = arcpy.GetParameterAsText(3)
includeEndPoints = 'NO_END_POINTS'
inputLineFLsplit = arcpy.GetParameterAsText(1)
inputPointFLsplit = arcpy.GetParameterAsText(2)
outputFCsplit = arcpy.GetParameterAsText(4)

arcpy.env.overwriteOutput = True

mxd = arcpy.mapping.MapDocument('CURRENT')
df = arcpy.mapping.ListDataFrames(mxd)[0]

#Generate points along line for split
arcpy.SetProgressorLabel("Generating points to split by...")
arcpy.GeneratePointsAlongLines_management(inputLineFLpoints, outputPointFC, 'DISTANCE', splitDistance,Include_End_Points = includeEndPoints)

#Split line into separate segments based on previous points with a 2 meter radius tolerance around the point
arcpy.SetProgressorLabel("Splitting initial line into segments...")
arcpy.SplitLineAtPoint_management(inputLineFLsplit,outputPointFC, outputFCsplit, search_radius = '2 Meters')

# Get filename part of outputFCsplit
flName = os.path.basename(outputFCsplit)

#Create a feature layer to be used for AddGeometryAttributes
arcpy.MakeFeatureLayer_management(outputFCsplit,flName)

#Create a layer object from the feature layer
tempLayer = arcpy.mapping.Layer(flName)

#Add attributes for line start,mid, and end to determine order of segments for new feature classes; for some reason line segments are not in proper order
arcpy.AddGeometryAttributes_management(flName,"LINE_START_MID_END")

#Add layer to the map
arcpy.mapping.AddLayer(df,tempLayer)





