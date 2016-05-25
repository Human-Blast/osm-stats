import sys
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

    _idsDateMap = {}

    _idsNode = {}

    _idsValidation = {}

    _nodeCounter = 1

    _waysCounter = 1

    _iteration = 1

    def _Reset(self):
        self._outfile = None
        self._isWay = False
        self._targetDate = None
        self._idsDateMap = {}
        self._idsNode = {}
        self._idsValidation = {}
        self._nodeCounter = 1
        self._waysCounter = 1
        self._iteration = 1

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

            if self._iteration == 1: 
                elId = attrib["id"]
                if self._idsDateMap.has_key(elId):
                    prevElementDate = self._idsDateMap[elId]
                    if date > prevElementDate:
                        self._idsDateMap[elId] = date
                else:
                    self._idsDateMap[elId] = date
            elif self._iteration == 2:
                elId = attrib["id"]
                if self._idsDateMap.has_key(elId) == False:
                    raise "Element with id not found" + str(elId)
                mapDate = self._idsDateMap[elId] 
                if mapDate != date:
                    return
            else:
                raise "Unsupported iteration " + str(self._iteration)


        if name == "node":
            # check close way tag
            if self._isWay:
                self._outfile.write("</way>\n"); 
                self._isWay = False

            nodeId = attrib["id"]

            if self._iteration == 2:
                # Generate increasing node id
                newNodeId = str(self._nodeCounter)
                self._idsNode[nodeId] = newNodeId
                nodeId = newNodeId
                self._nodeCounter += 1

            outStr = "<node id='{0}' lat='{1}' lon='{2}' timestamp='{3}' />\n".format(nodeId, attrib["lat"], attrib["lon"], dateStr)
            self._outfile.write(outStr); 
        elif name == "way":
            wayId = attrib["id"]
            if self._iteration == 2:
                # Validate result
                if self._idsValidation.has_key(wayId):
                    errStr = "Found duplicate id:" + str(wayId) + " " + str(dateStr)
                    print errStr
                    print "idsDateMap: " + str(self._idsDateMap[wayId])
                    raise errStr
                self._idsValidation[wayId] = True

                # Generate increasing wys id
                wayId = str(self._waysCounter)
                self._waysCounter += 1

            outStr = "<way id='{0}' timestamp='{1}'>\n".format(wayId, dateStr)
            self._outfile.write(outStr);
            self._isWay = True
        elif name == "nd":
            refId = attrib["ref"]
            if self._iteration == 2:
                # Generate increasing node id
                if self._idsNode.has_key(refId):
                    refId = self._idsNode[refId]
                else:
                    return# don't write invalid nodes
            outStr = "<nd ref='{0}'/>\n".format(refId)
            self._outfile.write(outStr); 
        elif name == "tag":
            if attrib["k"] == "highway":
                try: 
                    outStr = "<tag k='{0}' v='{1}' />\n".format(attrib["k"], attrib["v"])
                    self._outfile.write(outStr); 
                except:
                    return

    def end_element(self, name):
         if name == "way":
            if self._isWay:
                self._outfile.write("</way>\n"); 
                self._isWay = False

    def ExtractHistory(self, filename, targetDateStr, countryName):
        
        self._Reset()

        self._targetDate = datetime.datetime.strptime(targetDateStr, "%Y-%m-%dT%H:%M:%SZ")
        outfilename = "history_iteration2.osm"
        print "Dump history to file:", outfilename

        # Iteration 1

        print "Run Iteration 1"

        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element

        iteration1filename = "history_iteration1.osm"
        self._iteration = 1
        self._outfile = open(iteration1filename, "w")
        with self._outfile:    
            self._outfile.write("<osm timestamp='{0}'>\n".format(targetDateStr)) 
            with open(filename, "r") as fpR:    
                p.ParseFile(fpR)
            self._outfile.write("</osm>")

        # Iteration 2
        print "Run Iteration 2"

        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element

        self._iteration = 2
        self._nodeCounter = 1
        self._outfile = open(outfilename, "w")
        with self._outfile:    
            self._outfile.write("<osm timestamp='{0}'>\n".format(targetDateStr)) 
            with open(iteration1filename, "r") as fpR:    
                p.ParseFile(fpR)
            self._outfile.write("</osm>")

        return outfilename

def ExtractHistory(filename, targetDateStr, countryName):
    parser = OSMHistoryParser()
    outfilename = parser.ExtractHistory(filename, targetDateStr, countryName)
    return outfilename
