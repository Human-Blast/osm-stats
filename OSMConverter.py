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

if os.name == "nt":
    # Setup windows enviroment
    curAbsPath = os.path.dirname(os.path.abspath(__file__))
    osmconvPath = curAbsPath + "\Win32\OsmConv"
    os.environ["PATH"] = os.environ["PATH"] + ";" + osmconvPath + ";"


def ConvertFile(spatPoly, filename, postfix, usePbf=False):
        if usePbf:
            outputfile = "convert" + str(postfix) + ".pbf"
        else:
            outputfile = "convert" + str(postfix) + ".osm"
        if os.path.isfile(outputfile):
            os.remove(outputfile) 

        if os.path.isfile(filename) == False:
            err = "File not found:" + str(filename)
            print err
            raise err

        fname, file_extension = os.path.splitext(filename)
        isNeedDecompress = False
        if file_extension == ".bz2":
            isNeedDecompress = True
        elif file_extension == ".osm":
            return filename # no convert required

        appName = ""
        if os.name == "nt":
            appName = "osmconvert"
        else :
            appName = "./osmconvert64"

        convertPipe = subprocess.Popen([appName, 
             "-", 
             "-B=" + spatPoly,
             "-o=" + outputfile, 
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
                    else :
                        targetData = fileData

                    if targetData == None or targetData == "":
                        continue

                    convertPipe.stdin.write(targetData)
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise

        convertPipe.stdin.close()
        convertPipe.wait()


        return outputfile

def ConvertUrl(spatPoly, url, postfix, usePbf=False):
        if usePbf:
            outputfile = "convert" + str(postfix) + ".pbf"
        else:
            outputfile = "convert" + str(postfix) + ".osm"

        if os.path.isfile(outputfile):
            os.remove(outputfile) 

        parsed_uri = urlparse( url )
        serverUrl = '{uri.netloc}'.format(uri=parsed_uri)
        page = '{uri.path}'.format(uri=parsed_uri)

        appName = ""
        if os.name == "nt":
            appName = "osmconvert"
        else :
            appName = "./osmconvert64"

        convertPipe = subprocess.Popen([appName, 
             "-", 
             "-B=" + spatPoly,
             "-o=" + outputfile, 
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
                else:
                    targetData = respData

                if targetData == None or targetData == "":
                    continue

                convertPipe.stdin.write(targetData)
            except:
                print "Unexpected error:", sys.exc_info()[0]
                raise

        convertPipe.stdin.close()
        convertPipe.wait()

        return outputfile