from osgeo import ogr
from osgeo import osr

class StaticsticRes:
    Length = 0
    Count = 0


def GetQueryBox(shpBoundFilename):
    dsBound = ogr.Open( shpBoundFilename )  
    lyrBound = dsBound.GetLayer(0)
    geomBound = None
    boundFeat = lyrBound.GetNextFeature()
    geomBound = boundFeat.GetGeometryRef()
    env = geomBound.GetEnvelope()
    boundFeat.Destroy()
    return {"s": str(env[2]), "w": str(env[1]), "n": str(env[3]), "e": str(env[0])}


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


def CalculateLengths(filename, highwayTypes, shpBoundFilename):

    dsBound = ogr.Open( shpBoundFilename )  
    lyrBound = dsBound.GetLayer(0)
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