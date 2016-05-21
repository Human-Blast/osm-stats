import sys  
import os
import httplib
import urllib
import time
import string
import codecs
import thread
import threading
import StringIO
import subprocess
import bz2
from urlparse import urlparse


overpassServerUrl = "overpass-api.de"
overpassPage = "/api/interpreter"


def GetResponseOverpass(overpassServerUrl, overpassPage, bbox, strDate):
        # specify we're sending parameters that are url encoded
        # he order of values in the bounding box (51.249,7.148,51.251,7.152) is minimum latitude, minimum longitude, maximum latitude, maximum longitude (or South-West-North-East).
        boxStr = bbox["s"] + "," + bbox["w"] + "," + bbox["n"] + "," + bbox["e"]
        data = "[date:\"" + strDate + "\"];"
        data += "(node(" + boxStr + ");way(" + boxStr + "););out;" 
        params = urllib.urlencode({'data': data})
        headers = {"Content-type": "application/x-www-form-urlencoded", 
                "Accept": "text/plain"}
        conn = httplib.HTTPConnection(overpassServerUrl)
        conn.request("POST", overpassPage, params, headers)
        response = conn.getresponse()
        return response

def GetOverpassOSMData(bbox, strDate):
    s = float(bbox["s"])
    n = float(bbox["n"])
    w = float(bbox["w"])
    e = float(bbox["e"])
    height = abs(s - n)
    width = abs(w - e)
    if max(height, width) < 3:
        fName = "source.osm"
        GetOverpassOSMDataSingle(fName, bbox, strDate)
        return [fName]
    else:
        count = int(round(max(height, width) / 4))
        stepX = (e - w) / count
        stepY = (n - s) / count
        x = w
        y = s
        outFNames = []
        for i  in range(0, count):
            newBbox = { "s" : str(y), "n": str(y + stepY), "w" : str(x), "e" : str(x + stepX)  }
            fName = "source" + str(i) + ".osm"
            try:
                GetOverpassOSMDataSingle(fName, newBbox, strDate)  
                outFNames.append(fName)
            except:
                print "Warning error in coordinate " + str(x) + "," + str(y)

            x += stepX      
            y += stepY
        return outFNames


def GetOverpassOSMDataSingle(filename, bbox, strDate):

        tryCounter = 0
        
        while(True):
            response = GetResponseOverpass(overpassServerUrl, overpassPage, bbox, strDate)
            print response.status, response.reason
            
            if response.status == 429: #Too Many Requests
                time.sleep(70) # delays for 70 seconds
                tryCounter += 1
                if tryCounter > 5:
                    raise Exception("Can't download data Too Many Requests")
                continue

            if response.status == 200:
                break
            raise Exception("Can't download data")

        print "Downloading data..."

        with codecs.open(filename, "w", "utf-8") as osmFile:
            fileLen = response.length
            chunckSize = 20000
            while(True):
                respData = response.read(chunckSize)
                if(respData == None or respData == ""):
                    break
                try:
                    respDataUnicode = unicode(respData, "utf-8", errors='replace')
                    osmFile.write(respDataUnicode)
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise
                osmFile.flush()

        return filename


def GetUrlOSMData(bbox, url):
        outSHPFolder = "outshp"
        outputfile = "./" + outSHPFolder + "/lines.shp"
        if os.path.isfile(outputfile):
            os.remove(outputfile) 

        xmin = bbox["w"]
        ymin = bbox["s"]
        xmax = bbox["e"]
        ymax = bbox["n"]

        parsed_uri = urlparse( url )
        serverUrl = '{uri.netloc}'.format(uri=parsed_uri)
        page = '{uri.path}'.format(uri=parsed_uri)

        #-spat xmin ymin xmax ymax
        ogr2ogrPipe = subprocess.Popen(['ogr2ogr', "-f", "ESRI Shapefile", outSHPFolder, "/vsistdin/", 
             "-overwrite", "-skipfailures",
             "-spat", xmin, ymin, xmax, ymax, 
             ], stdout=subprocess.PIPE, stdin=subprocess.PIPE)

        fname, file_extension = os.path.splitext(page)
        isNeedDecompress = False
        if file_extension == ".bz2":
            isNeedDecompress = True
                
        decompressor = bz2.BZ2Decompressor()

        tryCounter = 0
        
        while(True):
            conn = httplib.HTTPConnection(serverUrl)
            conn.request("GET", page)
            response = conn.getresponse()
            print response.status, response.reason
            
            if response.status != 200: #web error
                time.sleep(70) # delays for 70 seconds # To many request case
                tryCounter += 1
                if tryCounter > 3:
                    raise Exception("Can't download data")
                continue

            if response.status == 200:
                break
            raise Exception("Can't download data")

        print "Downloading data..."

        progressLen = 0.0
        progressLenSumm = 0.0

        fileLen = response.length
        chunkSize = 1000000
        while(True):
            respData = response.read(chunkSize)
            if(respData == None or respData == ""):
                break

            progressLenSumm += chunkSize / 1048576.0
            progressLen += chunkSize / 1048576.0
            if progressLen > 512:
                print "Processing MB: " + str(progressLenSumm)
                progressLen = 0.0

            try:
                targetData = ""
                if isNeedDecompress:
                    while(True):
                        try:
                            targetData += decompressor.decompress(respData)
                            unusedData = decompressor.unused_data
                            if unusedData != "" and unusedData != None:
                                decompressor = bz2.BZ2Decompressor()
                                respData = unusedData
                                continue
                            break
                        except EOFError:
                            unusedData = decompressor.unused_data
                            decompressor = bz2.BZ2Decompressor()
                            if unusedData != "" and unusedData != None:
                                respData = unusedData + respData

                if targetData == None or targetData == "":
                    continue

                ogr2ogrPipe.stdin.write(targetData)
            except:
                print "Unexpected error:", sys.exc_info()[0]
                raise

        ogr2ogrPipe.stdin.close()
        ogr2ogrPipe.wait()

        return outputfile



def GetFileOSMData(bbox, filename):
        outSHPFolder = "outshp"
        outputfile = "./" + outSHPFolder + "/lines.shp"
        if os.path.isfile(outputfile):
            os.remove(outputfile) 

        xmin = bbox["w"]
        ymin = bbox["s"]
        xmax = bbox["e"]
        ymax = bbox["n"]
        
        fname, file_extension = os.path.splitext(filename)
        isNeedDecompress = False
        if file_extension == ".bz2":
            isNeedDecompress = True
        if file_extension == ".shp":
            return filename # no any extract

        #else:
        #    return filename # if file not compress no action

        #-spat xmin ymin xmax ymax
        ogr2ogrPipe = subprocess.Popen(['ogr2ogr', "-f", "ESRI Shapefile", outSHPFolder, "/vsistdin/", 
             "-overwrite", "-skipfailures",
             "-spat", xmin, ymin, xmax, ymax, 
             ], stdout=subprocess.PIPE, stdin=subprocess.PIPE)

                
        decompressor = bz2.BZ2Decompressor()

        tryCounter = 0
     
        print "Extract data..."

        progressLen = 0.0
        progressLenSumm = 0.0

        chunkSize = 2000000
        with open(filename, "rb") as fp:
            while(True):
                fileData = fp.read(chunkSize)
                if(fileData == None or fileData == ""):
                    break

                progressLenSumm += chunkSize / 1048576.0
                progressLen += chunkSize / 1048576.0
                if progressLen > 512:
                    print "Processing MB: " + str(progressLenSumm)
                    progressLen = 0.0

                try:
                    targetData = ""
                    if isNeedDecompress:
                         while(True):
                            try:
                                targetData += decompressor.decompress(fileData)
                                unusedData = decompressor.unused_data
                                if unusedData != "" and unusedData != None:
                                   decompressor = bz2.BZ2Decompressor()
                                   fileData = unusedData
                                   continue
                                break
                            except EOFError:
                                unusedData = decompressor.unused_data
                                decompressor = bz2.BZ2Decompressor()
                                if unusedData != "" and unusedData != None:
                                    fileData = unusedData + fileData

                    if targetData == None or targetData == "":
                        continue

                    ogr2ogrPipe.stdin.write(targetData)
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise

        ogr2ogrPipe.stdin.close()
        ogr2ogrPipe.wait()

        return outputfile