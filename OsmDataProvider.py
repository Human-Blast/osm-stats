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

def GetOverpassOSMData(bbox, strDate, countryname):
    s = float(bbox["s"])
    n = float(bbox["n"])
    w = float(bbox["w"])
    e = float(bbox["e"])
    height = abs(s - n)
    width = abs(w - e)
    if max(height, width) < 3:
        fName = "convert.osm"
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
            fName = "convert_" + str(i) + ".osm"
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
