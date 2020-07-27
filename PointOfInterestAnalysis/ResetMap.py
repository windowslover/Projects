#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Jason
#
# Created:     16/04/2018
# Copyright:   (c) Jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
        import arcpy

        #Set workspace
        workspacePath = arcpy.GetParameterAsText(0)
        arcpy.env.workspace = workspacePath

        #Set variables
        mxd = arcpy.mapping.MapDocument('CURRENT')
        df = arcpy.mapping.ListDataFrames(mxd)[0]
        #searchTerm = 'MiniGolf'
        searchTerm =  arcpy.GetParameterAsText(1)

        layerList = arcpy.mapping.ListLayers(mxd,'*'+searchTerm+'*',df)

        #Remove mini golf layers
        for layer in layerList:
            arcpy.mapping.RemoveLayer(df,layer)


        print 'Done removing mini golf layers'

        layerList = arcpy.mapping.ListLayers(mxd,'states',df)

        #Remove states layer
        for layer in layerList:
            arcpy.mapping.RemoveLayer(df,layer)

        print 'Done removing states layer'

        #Remove files
        fileList = arcpy.ListFeatureClasses('*'+searchTerm+'*')

        for fileFc in fileList:
            arcpy.Delete_management(fileFc) ## **** Only seems to work on the second run in ArcMap

        print 'Done deleting feature classes'

        #Delete nnDistance table
        tableList = arcpy.ListTables('nnDistance')
        for table in tableList:
            arcpy.Delete_management(table)

        print 'Done deleting nnDistance table'

        #Check that user is running off a currently saved mxd
        if mxd.filePath != '':
            mxd.save()

if __name__ == '__main__':
    main()
