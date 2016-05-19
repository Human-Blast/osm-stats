import sys
import httplib
import datetime
import time
import xml.etree.ElementTree as etree
import bz2
import os
from urlparse import urlparse

def GetDateFromXMLOSM(filename):
    counter = 0
    for event, elem in etree.iterparse(filename, events=('start', 'end')):
        
        if elem.tag == "osm":
            date = elem.attrib["timestamp"]
            if date != "":
                return date

        if elem.tag == "meta":
            date = elem.attrib["osm_base"]
            if date != "":
                return date

        counter += 1
        if counter > 100:
            break

    raise "Can't get Date"

def GetDateFromBZ2(filename):
    counter = 0

    decompressor = bz2.BZ2Decompressor()
    
    with open(filename, "rb") as fp:
        fileData = fp.read(300000)
        if(fileData == '' or fileData == None):
            raise "Can't get Date"
        fileData = decompressor.decompress(fileData)
        with open("temp.osm", "wb") as fpW:
            fpW.write(fileData)    

    for event, elem in etree.iterparse("temp.osm", events=('start', 'end')):
        
        if elem.tag == "osm":
            date = elem.attrib["timestamp"]
            if date != "":
                return date

        if elem.tag == "meta":
            date = elem.attrib["osm_base"]
            if date != "":
                return date

        counter += 1
        if counter > 100:
            break
    return ""


def GetDateFromFile(filename):
        fname, file_extension = os.path.splitext(filename)
        if file_extension == ".bz2":
            return GetDateFromBZ2(filename)
        elif file_extension == ".osm":
            return GetDateFromXMLOSM(filename)
        else:
            raise "file not supported"
    

def GetDateFromUrl(url):
        parsed_uri = urlparse( url )
        serverUrl = '{uri.netloc}'.format(uri=parsed_uri)
        page = '{uri.path}'.format(uri=parsed_uri)

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


        respData = response.read(100000)
        if(respData == None or respData == ""):
            raise "Can't extract date"

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
            raise "Can't extract date"

        with open("temp.osm", "wb") as fpW:
            fpW.write(targetData)

        return GetDateFromXMLOSM("temp.osm")
