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
            outfilename = "spat-" + shortName + ".poly"
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
        if name not in countryNames:
            countryNames.append(name)

    return countryNames
