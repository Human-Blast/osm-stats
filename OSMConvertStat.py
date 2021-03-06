﻿import os
import sys
import codecs
import time
import thread
import threading
import subprocess
import datetime
import csv

#
# Description of statistic fields
#
StatFieldOneWay = "one_way"
# Turn Restrictions
StatFieldTurnRestrict = "turn_restrict"
# Roads with Names (i.e. Elm Street)
StatFieldRoadsWithNames = "roads_with_names"
# Roads with Designation (vs name - i.e. Interstate I-70, State Road 324, etc.)
StatFieldRoadsWithDesignation = "roads_with_designation"
# Roads with Different/Secondry Languages other than local language let's look for these secondary languages initially: English Spanish French Mandarin Portuguese
StatFieldRoadsWithSecondLang = "roads_with_second_lang"

StatFieldNewObjects = "new_objects"
StatFieldModifiedObjects = "modified_objects"
StatFieldDeletedObjects = "deleted_objects"


class StaticsticRes:
    Length = 0
    Count = 0



class StaticsticRes:
    Country = ""
    Year = 0
    Week = 0
    Kind = ""
    Length = 0
    Count = 0


def GetStatisticFromFile(filename, highwayTypes):
        
        res = {}
        for hType in highwayTypes:
            res[hType] = StaticsticRes()
        # Add other statistic fields
        res[StatFieldOneWay] = StaticsticRes()
        res[StatFieldTurnRestrict] = StaticsticRes()
        res[StatFieldRoadsWithNames] = StaticsticRes()
        res[StatFieldRoadsWithDesignation] = StaticsticRes()
        res[StatFieldRoadsWithSecondLang] = StaticsticRes()
        res[StatFieldNewObjects] = StaticsticRes()
        res[StatFieldModifiedObjects] = StaticsticRes()
        res[StatFieldDeletedObjects] = StaticsticRes()

        if os.path.isfile(filename) == False:
            print "Warning, statistic missing:" + str(filename)
            return res

        with open(filename, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in reader:
                if row[0] == "oneway":
                    res[StatFieldOneWay].Count = int(row[2])
                    res[StatFieldOneWay].Length = float(row[3])
                elif row[0] == "name":
                    res[StatFieldRoadsWithNames].Count = int(row[2])
                    res[StatFieldRoadsWithNames].Length = float(row[3])
                elif row[0] == "ref":
                    res[StatFieldRoadsWithDesignation].Count = int(row[2])
                    res[StatFieldRoadsWithDesignation].Length = float(row[3])
                elif row[0] == "newObjects":
                    res[StatFieldNewObjects].Count = int(row[2])
                    res[StatFieldNewObjects].Length = float(row[3])
                elif row[0] == "modifiedObjects":
                    res[StatFieldModifiedObjects].Count = int(row[2])
                    res[StatFieldModifiedObjects].Length = float(row[3])
                elif row[0] == "deletedObjects":
                    res[StatFieldDeletedObjects].Count = int(row[2])
                    res[StatFieldDeletedObjects].Length = float(row[3])
                elif row[0] == "severalLangs":
                    res[StatFieldRoadsWithSecondLang].Count = int(row[2])
                    res[StatFieldRoadsWithSecondLang].Length = float(row[3])
                elif row[0] == "turnRestrict":
                    res[StatFieldTurnRestrict].Count = int(row[2])
                    res[StatFieldTurnRestrict].Length = float(row[3])
                elif row[0] == "highway":
                    highwayVal = row[1]
                    res[highwayVal].Count = int(row[2])
                    res[highwayVal].Length = float(row[3])
                



        return res

def GetStatistic(filename, strDate, highwayTypes, postfix):
    outputfile = "convstat" + postfix + ".csv"

    if os.path.isfile(outputfile):
         os.remove(outputfile) 
         

    # "test.pbf" --out-statistics --stat-timestamp="2016-05-31T23:59:30Z" -tagsStats="highway,highway,oneway" -tagsVals="primary,motorway,yes" -statfile="out.csv"
    appName = ""
    if os.name == "nt":
        appName = "osmconvert"
    else :
        appName = "./osmconvert64"


    tagsStats = ""
    tagsVals = ""


    for highwayType in highwayTypes:
        tagsStats += "highway"
        tagsVals += highwayType
        tagsStats += ","
        tagsVals += ","

    tagsStats += "oneway,"
    tagsVals += "yes,"

    tagsStats += "name,"
    tagsVals += "*,"

    tagsStats += "ref"
    tagsVals += "*"

    sourcedate = datetime.datetime.strptime(strDate, "%Y-%m-%dT%H:%M:%SZ")
    startDate = sourcedate - datetime.timedelta(days=7)
    startDateStr = startDate.strftime("%Y-%m-%dT%H:%M:%SZ")

    convertPipe = subprocess.Popen([appName, 
            filename,             
            "--out-statistics",
            "--stat-timestamp=" + strDate,
            "--stat-timestamp-start=" + startDateStr,
            "--max-objects=1400000000",
            "-tagsStats=" + tagsStats,
            "-tagsVals=" + tagsVals,
            "-statfile=" + outputfile
            ], stdout=sys.stdout)
    retcode = convertPipe.wait()
    if retcode != 0:
        raise "Can't extract statistic"

    return GetStatisticFromFile(outputfile, highwayTypes)
