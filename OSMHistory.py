import sys
import os
import httplib
import datetime
import time
import xml.etree.ElementTree as etree
import bz2
import os
from urlparse import urlparse
import xml.parsers.expat


class OSMHistoryParser(object):

    _outfile = None

    _isWay = False

    _targetDate = None

    _nodeCounter = 1

    _idsNode = {}

    _idsValidation = {}

    _waysCounter = 1

    _outStr = ""

    _prevId = ""

    _prevType = ""

    _prevElementDate = None

    _chars_to_remove = ['&', '"', '\'', '<', '/', '>']

    _nodeInWayCounter = 0

    def _Reset(self):
        self._outfile = None
        self._isWay = False
        self._targetDate = None
        self._idsNode = {}
        self._idsValidation = {}
        self._nodeCounter = 1
        self._waysCounter = 1
        self._prevElementDate = None
        self._prevId = ""
        self._prevType = ""
        self._nodeInWayCounter = 0

    def _fastDateParse(self, val):
        return datetime.datetime(
            # "%Y-%m-%dT%H:%M:%SZ"
            int(val[0:4]), # %Y
            int(val[5:7]), # %m
            int(val[8:10]), # %d
            int(val[11:13]), # %H
            int(val[14:16]), # %M
            int(val[17:19]) # %S
        )

    def start_element(self, name, attrib):
        if self._isWay and (name == "tag" or name == "nd"):
            pass    
        elif name != "node" and name != "way":
            return
        
        dateStr = ""

        if name == "node" or name == "way":
            if attrib.has_key("timestamp") == False:
                return
            dateStr = attrib["timestamp"]
            if dateStr == "":
                return

            date = self._fastDateParse(dateStr)
                
            if date > self._targetDate:
                return# Skip futures dates

            elId = attrib["id"]
            if self._prevId != elId or self._prevType != name:
                if self._outStr != "":
                    # Validate result
                    key = self._prevType + self._prevId
                    if self._idsValidation.has_key(key):
                        errStr = "Found duplicate id:" + str(self._prevId) + " " + str(self._prevType)
                        print errStr
                        raise errStr
                    self._idsValidation[key] = True

                    self._outfile.write(self._outStr); 
                    self._outStr = ""

                    if self._prevType == "node":
                        # Generate increasing node id
                        self._idsNode[self._prevId] = str(self._nodeCounter)
                        self._nodeCounter += 1
                    elif self._prevType == "way":
                        self._waysCounter += 1
                    else:
                        raise "Not supported type: " + str(self._prevType)

                self._prevId = elId
                self._prevType = name
                self._prevElementDate = date


            if date < self._prevElementDate:
                return # skip old items

            self._outStr = ""


        if name == "node":            
            nodeId = str(self._nodeCounter)

            self._outStr = "<node id=\"{0}\" lat=\"{1}\" lon=\"{2}\" timestamp=\"{3}\" />\n".format(nodeId, attrib["lat"], attrib["lon"], dateStr)
        elif name == "way":            
            # Generate increasing wys id
            wayId = str(self._waysCounter)

            self._outStr += "<way id=\"{0}\" timestamp=\"{1}\">\n".format(wayId, dateStr)
            self._isWay = True
            self._nodeInWayCounter = 0
        elif name == "nd":
            if self._nodeInWayCounter >= 1999: # limit of GDAL
                return# Skip nodes to fix Too many nodes referenced in way

            refId = attrib["ref"]
            # Generate increasing node id
            if self._idsNode.has_key(refId):
                refId = self._idsNode[refId]
            else:
                return# don't write invalid nodes
            self._outStr += "<nd ref=\"{0}\"/>\n".format(refId)
            self._nodeInWayCounter += 1

        elif name == "tag":
            if attrib["k"] != "":
                try: 
                    v = attrib["v"]
                    if attrib["k"] == "note":
                        return
                    v = str(v).translate(None, ''.join(self._chars_to_remove))
                    self._outStr += "<tag k=\"{0}\" v=\"{1}\" />\n".format(attrib["k"], v)
                except:
                    return

    def end_element(self, name):
         if name == "way":
            if self._isWay:
                self._outStr += "</way>\n" 
                self._isWay = False
                self._nodeInWayCounter = 0

    def ExtractHistory(self, filename, targetDateStr, countryName):
        
        self._Reset()

        self._targetDate = datetime.datetime.strptime(targetDateStr, "%Y-%m-%dT%H:%M:%SZ")
        outfilename = "history_out.osm"
        print "Dump history to file:", outfilename
        
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element

        self._nodeCounter = 1
        self._outfile = open(outfilename, "w")
        with self._outfile:    
            self._outfile.write("<osm timestamp='{0}'>\n".format(targetDateStr)) 
            with open(filename, "r") as fpR:
                p.ParseFile(fpR)
            
            # check if not yet write
            if self._outStr != "":
                # write final node
                self._outfile.write(self._outStr)

            self._outfile.write("</osm>")

        return outfilename
    

def ExtractHistory(filename, targetDateStr, countryName):
    parser = OSMHistoryParser()
    outfilename = parser.ExtractHistory(filename, targetDateStr, countryName)
    return outfilename
