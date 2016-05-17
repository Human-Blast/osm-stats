# Setup GDAL enviroment
import os

if os.name == "nt":
    # Setup windows enviroment
    curAbsPath = os.path.dirname(os.path.abspath(__file__))
    gdalPath = curAbsPath + "\Win32\GDAL"
    os.environ["PATH"] = os.environ["PATH"] + ";" + gdalPath + ";"
    os.environ["GDAL_DATA"] = gdalPath + "\gdal-data"
    os.environ["GDAL_DRIVER_PATH"] = gdalPath + "\gdalplugins"

from osgeo import ogr
from osgeo import gdal
from osgeo import osr

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

def GetQueryBox(shpBoundFilename):
    dsBound = ogr.Open( shpBoundFilename )  

    lyrBound = dsBound.GetLayer()
    geomBound = None
    boundFeat = lyrBound.GetNextFeature()
    geomBound = boundFeat.GetGeometryRef()
    env = geomBound.GetEnvelope()
    boundFeat.Destroy()
    return {"s": str(env[2]), "w": str(env[0]), "n": str(env[3]), "e": str(env[1])}


def GetLengths(layer, highwayTypes, boundGeom):
    res = {}
    for hType in highwayTypes:
        res[hType] = StaticsticRes()

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


def GetStatistic(filename, highwayTypes, shpBoundFilename):

    dsBound = ogr.Open( shpBoundFilename )  
    lyrBound = dsBound.GetLayer()
    geomBound = None
    boundFeat = lyrBound.GetNextFeature()
    geomBound = boundFeat.GetGeometryRef()

    ds = ogr.Open( filename )    
    if ds is None:
         "ERROR: can't open osm file"
    
    for idx in range(0, ds.GetLayerCount()):
        lyr = ds.GetLayer(idx)
        geomType = lyr.GetGeomType()
        if geomType == 2:
            return GetLengths(lyr, highwayTypes, geomBound)
            break

    return None