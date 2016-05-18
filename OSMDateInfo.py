import sys
import httplib
import datetime
import time
import xml.etree.ElementTree as etree
import bz2
import os

def GetDateFromXMLOSM(filename):
    counter = 0
    for event, elem in etree.iterparse(filename, events=('start', 'end')):
        if elem.tag == "meta":
            return elem.attrib["osm_base"]
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
        if elem.tag == "meta":
            return elem.attrib["osm_base"]
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
    