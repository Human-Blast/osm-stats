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

    _iteration = 1

    def _fastDateParse(self, val):
        return datetime.datetime(
            # "%Y-%m-%dT%H:%M:%SZ"
            int(val[0:4]), # %Y
            int(val[5:7]), # %m
            int(val[8:10]) # %d
        ).date()

    def start_element(self, name, attrib):
        if self._isWay and (name == "tag" or name == "nd"):
            pass    
        elif name != "node" and name != "way":
            return
        
        if name == "node" or name == "way" or name == "relation":
            if attrib.has_key("timestamp"):
                dateStr = attrib["timestamp"]
                if dateStr != "":
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
            outStr = "<node id='{0}' lat='{1}' lon='{2}' />\n".format(attrib["id"], attrib["lat"], attrib["lon"])
            self._outfile.write(outStr); 
        elif name == "way":
            outStr = "<way id='{0}'>\n".format(attrib["id"])
            self._outfile.write(outStr);
            self._isWay = True
        elif name == "nd":
            outStr = "<nd ref='{0}'/>\n".format(attrib["ref"])
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
            self._outfile.write("</way>\n"); 
            self._isWay = False

    def ExtractHistory(self, filename, targetDateStr):
        #etree.parse(filename)

        self._targetDate = datetime.datetime.strptime(targetDateStr, "%Y-%m-%dT%H:%M:%SZ").date()
        outfilename = "history_" + self._targetDate.strftime("%Y_%m_%d") + ".osm"
        print "Dump history to file:", outfilename
        

        # Iteration 1
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element

        iteration1filename = "history_iteration1.osm"
        self._iteration = 1
        self._outfile = open(iteration1filename, "w")
        with self._outfile:    
            self._outfile.write("<osm>\n") 
            with open(filename, "r") as fpR:    
                p.ParseFile(fpR)
            self._outfile.write("</osm>")

        # Iteration 2
        p = xml.parsers.expat.ParserCreate()
        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element

        self._iteration = 2
        self._outfile = open(outfilename, "w")
        with self._outfile:    
            self._outfile.write("<osm>\n") 
            with open(iteration1filename, "r") as fpR:    
                p.ParseFile(fpR)
            self._outfile.write("</osm>")

        return outfilename

def ExtractHistory(filename, targetDateStr):
    parser = OSMHistoryParser()
    outfilename = parser.ExtractHistory(filename, targetDateStr)
    return outfilename
