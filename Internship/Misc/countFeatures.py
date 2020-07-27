#-------------------------------------------------------------------------------
# Name:        Count Features
# Purpose:     Count the number of features within a list of feature classes
#
# Author:      Jason Bartling
#
# Created:     10/02/2018
# Copyright:   (c) Jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
    import arcpy

    # Set workspace to geodatabase for features to count
    arcpy.env.workspace = arcpy.GetParameterAsText(0)
    wildCardString = arcpy.GetParameterAsText(1)

    featureClassList = arcpy.ListFeatureClasses(wildCardString)

    featureClassCount=0
    totalFeatureCount = 0

    # Loop through featureClasses and count total features for all feature classes
    for fc in featureClassList:

        # individual feature count for each feature classes
        countFeatures = arcpy.GetCount_management(fc)

        #running total of all features; get first item of Result list which is the feature count
        totalFeatureCount += int(countFeatures.getOutput(0))

        # Increment feature class count
        featureClassCount+=1

    # Add message to display output with counts in output window for ArcMap
    arcpy.AddMessage('SCRIPT OUTPUT:  There were {0} feature classes and {1} total features.'.format(featureClassCount, totalFeatureCount))

if __name__ == '__main__':
    main()
