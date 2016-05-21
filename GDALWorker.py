import os
import sys
import codecs
import time
import thread
import threading
import StringIO
import subprocess

if os.name == "nt":
    # Setup windows enviroment
    curAbsPath = os.path.dirname(os.path.abspath(__file__))
    gdalPath = curAbsPath + "\Win32\GDAL"
    pythonPath = curAbsPath + "\Win32\Scripts"
    os.environ["PATH"] = os.environ["PATH"] + ";" + gdalPath + ";" + pythonPath
    os.environ["GDAL_DATA"] = gdalPath + "\gdal-data"
    os.environ["GDAL_DRIVER_PATH"] = gdalPath + "\gdalplugins"

from osgeo import ogr
from osgeo import gdal
from osgeo import osr

# print OGR drivers
#countDriver = ogr.GetDriverCount()
#for i in range(0, countDriver):
#    print ogr.GetDriver(i).GetName()

class StaticsticRes:
    Length = 0
    Count = 0


# example GDAL error handler function
def gdal_error_handler(err_class, err_num, err_msg):
    errtype = {
            gdal.CE_None:'None',
            gdal.CE_Debug:'Debug',
            gdal.CE_Warning:'Warning',
            gdal.CE_Failure:'Failure',
            gdal.CE_Fatal:'Fatal'
    }
    err_msg = err_msg.replace('\n',' ')
    err_class = errtype.get(err_class, 'None')
    print 'Error Number: %s' % (err_num)
    print 'Error Type: %s' % (err_class)
    print 'Error Message: %s' % (err_msg)


 # install error handler
gdal.PushErrorHandler(gdal_error_handler)

def GetQueryBox(shpBoundFilename, countryName):
    dsBound = ogr.Open(shpBoundFilename)  
    lyrBound = dsBound.GetLayer()
    env = None
    for feature in lyrBound:
        # get the input geometry
        geom = feature.GetGeometryRef()
        name = feature.GetField("NAME")
        if name.lower() == countryName.lower():
            env = geom.GetEnvelope()
            break            

    return {"w": str(env[0]), "e": str(env[1]), "s": str(env[2]), "n": str(env[3])}


def GetLengths(res, layer, highwayTypes, boundGeom):

    source = layer.GetSpatialRef()
    #print source.ExportToWkt()

    target = osr.SpatialReference()
    target.ImportFromEPSG(3857)# len in meters

    coordTrans = osr.CoordinateTransformation(source, target)

    layer.SetSpatialFilter(boundGeom)

    for feature in layer:
         # get the input geometry
        geom = feature.GetGeometryRef()
        highwayVal = feature.GetField("highway")
        if highwayVal != None: 
            if highwayVal in highwayTypes:
                # reproject the geometry
                geom.Transform(coordTrans)
                len = geom.Length()
                res[highwayVal].Length += len
                res[highwayVal].Count += 1
    return res

def keep_running():
    return True

def run_web_service():
    os.system('python WebService.py')    

def GetStatistic(filenames, highwayTypes, shpBoundFilename, countryName):

    
    dsBound = ogr.Open(shpBoundFilename)  
    lyrBound = dsBound.GetLayer()
    geomBound = None
    for feature in lyrBound:
        # get the input geometry
        geom = feature.GetGeometryRef()
        name = feature.GetField("NAME")
        if name.lower() == countryName.lower():
            geomBound = geom
            break            
    
    res = {}
    for hType in highwayTypes:
        res[hType] = StaticsticRes()

    for filename in filenames:

        ds = ogr.Open( filename)

        if ds is None:
             "ERROR: can't open osm file"

        for idx in range(0, ds.GetLayerCount()):
            lyr = ds.GetLayer(idx)
            geomType = lyr.GetGeomType()
            if geomType == 2:
                GetLengths(res, lyr, highwayTypes, geomBound)
                break

    return res