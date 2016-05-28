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

#
# Description of statistic fields
#
StatFieldOneWay = "one_way"
# Turn Restrictions
StatFieldTurnRestrict = "turn_restrict"
# Roads with Names (i.e. Elm Street)
StatFieldRoadsWithNames = "roads_with_names"
# Roads with Designation (vs name - i.e. Interstate I-70, State Road 324, etc.)
StatFieldRoadsWithDesignation = "roads_with_designation"
# Roads with Different/Secondry Languages other than local language let's look for these secondary languages initially: English Spanish French Mandarin Portuguese
StatFieldRoadsWithSecondLang = "roads_with_second_lang"

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

def GetShortCountryName(shpBoundFilename, countryName):
        dsBound = ogr.Open(shpBoundFilename)  
        lyrBound = dsBound.GetLayer()
        env = None
        for feature in lyrBound:
            # get the input geometry
            name = feature.GetField("NAME")
            if name.lower() == countryName.lower():
                name = feature.GetField("ISO2")
                if name == "":
                    raise "ISO2 not set for: " + countryName
                return name.lower()
        raise "Country not found : " + countryName

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
    if env == None:
        raise "Country not found : " + countryName
    return {"w": str(env[0]), "e": str(env[1]), "s": str(env[2]), "n": str(env[3])}

def CreatePolyFile(shpBoundFilename, countryName):
    dsBound = ogr.Open(shpBoundFilename)  
    lyrBound = dsBound.GetLayer()
    outfilename = None
    for feature in lyrBound:
        # get the input geometry
        geom = feature.GetGeometryRef()
        name = feature.GetField("NAME")
        if name.lower() == countryName.lower():
            shortName = feature.GetField("ISO2")
            outfilename = "spat.poly"
            with open(outfilename, "w") as fp:
                fp.write(str(shortName) + "\n")

                geomCount = geom.GetGeometryCount()
                geomTypeNameMain = geom.GetGeometryName()

                if geomTypeNameMain == "POLYGON":
                    fp.write("1\n")

                    geom = geom.ConvexHull()

                    # Get ring
                    geomRing = geom.GetGeometryRef(0)
                    pntsCount = geomRing.GetPointCount()
                    if pntsCount > 1000:
                        geom = geom.ConvexHull()
                        geomRing = geom.GetGeometryRef(0)
                        pntsCount = geomRing.GetPointCount()

                    for idx in range(0, pntsCount):
                        x = geomRing.GetX(idx)
                        y = geomRing.GetY(idx)
                        pntStr = "{0:.4e} {1:.4e}\n".format(x, y)
                        fp.write(pntStr)
                    fp.write("END\n")
                else:
                    for idxGeom in range(0, geomCount):
                        geomSub = geom.GetGeometryRef(idxGeom)
                        geomTypeName = geomSub.GetGeometryName()
                        if geomTypeName != "POLYGON":
                            print "Found invalid geometry : ", geomTypeName 
                            raise "Found invalid geometry"
                        
                        area = geomSub.Area()
                        if area < 0.5:
                            continue #ignore small areas

                        fp.write(str(idxGeom + 1) + "\n")

                        geomSubNew = geomSub.ConvexHull()
                        # Get ring
                        geomRing = geomSubNew.GetGeometryRef(0)
                        pntsCount = geomRing.GetPointCount()

                        if pntsCount == 0:
                            raise "Found empty polygon"

                        for idx in range(0, pntsCount):
                            x = geomRing.GetX(idx)
                            y = geomRing.GetY(idx)
                            pntStr = "    {0:.6E}   {1:.6E}\n".format(x, y)
                            fp.write(pntStr)
                        fp.write("END\n")


                fp.write("END\n")

            break            
    if outfilename == None:
        raise "Country not found : " + countryName
    return outfilename

def GetCountryNames(shpBoundFilename):

    countryNames = []

    dsBound = ogr.Open(shpBoundFilename)  
    lyrBound = dsBound.GetLayer()
    env = None
    for feature in lyrBound:
        # get the input geometry
        geom = feature.GetGeometryRef()
        name = feature.GetField("NAME")
        countryNames.append(name)

    return countryNames

# Add statistic for highway
def AddHighways(res, highwayTypes, feature, len):
        highwayVal = feature.GetField("highway")
        if highwayVal != None: 
            if highwayVal in highwayTypes:
                res[highwayVal].Length += len
                res[highwayVal].Count += 1

# Roads with Names (i.e. Elm Street)
def AddOneWay(res, feature, len, fieldNames):
    if fieldNames.has_key("oneway") == False:
        return
    onewayVal = feature.GetField("oneway")    
    highwayVal = feature.GetField("highway")

    # 1. Some tags (such as junction=roundabout, highway=motorway and others) imply oneway=yes
    # 2. If the oneway restriction is in the opposite direction to the drawn way, the fix in most cases is to turn the way around ("reverse way" tool in the map editors)
    #    and apply oneway=yes. If in a (very) rare case, the direction of the way cannot be changed, you can instead tag it as oneway=-1.
    if onewayVal == "yes" or onewayVal == "-1":
        res[StatFieldOneWay].Length += len
        res[StatFieldOneWay].Count += 1   

def AddTurn(res, feature, len, fieldNames):
    if fieldNames.has_key("turn") == False:
        return
    highwayVal = feature.GetField("highway")
    turnVal = feature.GetField("turn")    

    if turnVal != "" and turnVal != None:
        res[StatFieldTurnRestrict].Length += len
        res[StatFieldTurnRestrict].Count += 1   

def AddRoadsWithNames(res, feature, len, fieldNames):
    # Use the name=* and/or the ref=* for each section of the road (way) which has a name or reference.   
    nameVal = ""
    if fieldNames.has_key("name"):
        nameVal = feature.GetField("name")
    # In addition, where a road is now much more generally known by its reference (for example the 'A1' in the UK), 
    # but that it also has a current legal name for historical reasons 
    # if it probably better to leave the name field blank and put the name in alt_name which means that it is much less likely to be rendered.
    altNameVal = ""
    if fieldNames.has_key("alt_name"):
        altNameVal = feature.GetField("alt_name")

    ref = ""
    if fieldNames.has_key("ref"):
        ref = feature.GetField("ref")

    if (nameVal != "" and nameVal != None) or (altNameVal != "" and altNameVal != None):
        if ref != "" and ref != None:
            # Roads with Designation (vs name - i.e. Interstate I-70, State Road 324, etc.)
            res[StatFieldRoadsWithDesignation].Length += len
            res[StatFieldRoadsWithDesignation].Count += 1
        else:
            # Roads with Names (i.e. Elm Street)
            res[StatFieldRoadsWithNames].Length += len
            res[StatFieldRoadsWithNames].Count += 1

def AddRoadsWithSecondryLang(res, layer, feature, len, langNamesFields):
        counter = 0
        for fieldName in langNamesFields:
            nameVal = feature.GetField(fieldName)
            if nameVal != "" and nameVal != None:
                counter += 1
        if counter >= 2:
            res[StatFieldRoadsWithSecondLang].Length += len
            res[StatFieldRoadsWithSecondLang].Count += 1


def GetStatFromLayer(res, layer, highwayTypes, boundGeom):

    source = layer.GetSpatialRef()
    #print source.ExportToWkt()

    target = osr.SpatialReference()
    target.ImportFromEPSG(3857)# len in meters

    coordTrans = osr.CoordinateTransformation(source, target)

    layer.SetSpatialFilter(boundGeom)

    # Collect field names
    defn = layer.GetLayerDefn()
    fieldNames = {}
    for i in range(defn.GetFieldCount()):
        fieldname = defn.GetFieldDefn(i).GetName()
        fieldNames[fieldname] = True

    langNames = []
    langNamesFields = []
    for fieldNamePair in fieldNames.items():
        fieldName = fieldNamePair[0]
        if fieldName.startswith("name:"):
            langName = str(fieldName)
            langName = langName.replace("name:left:", "")
            langName = langName.replace("name:right:", "")
            langName = langName.replace("name:", "")
            # Roads with Different/Secondry Languages other than local language 
            langNames.append(fieldName)
            langNamesFields.append(fieldName)

    for feature in layer:
        highwayVal = feature.GetField("highway")
        if highwayVal == "" or highwayVal == None:
            continue

        # get the input geometry
        geom = feature.GetGeometryRef()
        # reproject the geometry to meters
        geom.Transform(coordTrans)
        # get length in meters
        len = geom.Length()

        AddHighways(res, highwayTypes, feature, len)
        AddOneWay(res, feature, len, fieldNames)
        AddTurn(res, feature, len, fieldNames)
        AddRoadsWithNames(res, feature, len, fieldNames)
        AddRoadsWithSecondryLang(res, layer, feature, len, langNamesFields)


    return res


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
    # Add other statistic fields
    res[StatFieldOneWay] = StaticsticRes()
    res[StatFieldTurnRestrict] = StaticsticRes()
    res[StatFieldRoadsWithNames] = StaticsticRes()
    res[StatFieldRoadsWithDesignation] = StaticsticRes()
    res[StatFieldRoadsWithSecondLang] = StaticsticRes()


    for filename in filenames:

        ds = ogr.Open( filename)

        if ds is None:
             "ERROR: can't open osm file"

        for idx in range(0, ds.GetLayerCount()):
            lyr = ds.GetLayer(idx)
            geomType = lyr.GetGeomType()
            if geomType == 2:# ways geometry type
                GetStatFromLayer(res, lyr, highwayTypes, geomBound)
                break

    return res