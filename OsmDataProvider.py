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
        filename = "source.osm"

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

        fileLen = response.length
        chunckSize = 200000
        while(True):
            respData = response.read(chunckSize)
            if(respData == None or respData == ""):
                break
            try:
                if isNeedDecompress:
                    respData = decompressor.decompress(respData)
                    if respData == None or respData == "":
                        continue
                ogr2ogrPipe.stdin.write(respData)
            except:
                print "Unexpected error:", sys.exc_info()[0]
                raise

        ogr2ogrPipe.stdin.close()
        ogr2ogrPipe.wait()

        return outputfile

def GetFileOSMData(bbox, filename):
        outputfile = "source.osm"
        
        if os.path.isfile(outputfile):
            os.remove(outputfile) 

        xmin = bbox["w"]
        ymin = bbox["s"]
        xmax = bbox["e"]
        ymax = bbox["n"]
        
        fname, file_extension = os.path.splitext(page)
        isNeedDecompress = False
        if file_extension == ".bz2":
            isNeedDecompress = True
        else:
            return filename # if file not compreses no action

        #-spat xmin ymin xmax ymax
        ogr2ogrPipe = subprocess.Popen(['ogr2ogr', "-f", "ESRI Shapefile", outSHPFolder, "/vsistdin/", 
             "-overwrite", "-skipfailures",
             "-spat", xmin, ymin, xmax, ymax, 
             ], stdout=subprocess.PIPE, stdin=subprocess.PIPE)

                
        decompressor = bz2.BZ2Decompressor()

        tryCounter = 0
     
        print "Parsing data..."

        chunckSize = 200000
        with open(filename) as fp:
            while(True):
                fileData = fp.read(chunkSize)
                if(fileData == None or fileData == ""):
                    break
                try:
                    if isNeedDecompress:
                        fileData = decompressor.decompress(fileData)
                        if fileData == None or fileData == "":
                            continue
                    ogr2ogrPipe.stdin.write(fileData)
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise

        ogr2ogrPipe.stdin.close()
        ogr2ogrPipe.wait()

        return outputfile