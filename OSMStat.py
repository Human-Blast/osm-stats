import sys
import os
import httplib
import datetime
import calendar
import time
import argparse
import multiprocessing
import OsmDataProvider
import GDALWorker
import OSMDateInfo
import OSMHistory
import OSMConverter
import StatDatabase


#
# Application parameters:
#

# Parameters of date region
updateDate = datetime.date(2016, 5, 16)
countOfWeeks = 1

# boundary of countries in shape format
shpBoundFilename = "./CountriesBounds/countries.shp"

highwayTypes = ["motorway", "secondary", 
                "secondary_link", "primary", "primary_link", 
                "tertiary", "residential", "unclassified",
                "road", "path", "service",
                "living_street", "track", "raceway"
                ]

countryNames = ["Haiti"]
# End of applications parameters


def MoveToNextWeek(sourcedate):
        d = sourcedate - datetime.timedelta(days=7)
        return d

def RunSinlge(strDate, postfix, lockCSV, args, countryName):
    lockCSV.acquire()
    date = datetime.datetime.strptime(strDate, "%Y-%m-%dT%H:%M:%SZ")
    csvDateStr = date.strftime("%d %B %Y")
    print csvDateStr
    lockCSV.release()

    filenames = []

    # first download OSM data 
    if args.overpass == "true":
        # download by Overpass_API
        print "Start download OSM data 'Overpass_API' "
        filenames = OsmDataProvider.GetOverpassOSMData(bbox, strDate, postfix)
    elif args.url != None:
        print "Start download OSM data 'url' " + args.url
        fName = OSMConverter.ConvertUrl(bbox, args.url, postfix)
        filenames.append(fName)
    elif args.inputfile != None:
        print "Parse OSM data 'inputfile' " + args.inputfile        
        fName = OSMConverter.ConvertFile(bbox, args.inputfile, postfix)
        filenames.append(fName)
    elif args.history != None:
        lockCSV.acquire()
        print "Start extract OSM data from history file: " + args.history
        lockCSV.release()
        
        fName = OSMHistory.ExtractHistory(args.history, strDate, postfix)
        filenames.append(fName)
    else:
        raise "not supported"

    lockCSV.acquire()
    print "Start calculate statistic..."
    lockCSV.release()

    res = GDALWorker.GetStatistic(filenames, highwayTypes, shpBoundFilename, countryName)

    lockCSV.acquire()
    
    print "Write to CSV..."

    outFile = open("output-" + countryName + ".csv", "a")
    countryShortName = GDALWorker.GetShortCountryName(shpBoundFilename, countryName)
    for key, value in res.iteritems():
        outStr = csvDateStr
        outStr += "," + countryShortName
        outStr += "," + key
        outStr += "," + str(value.Count)
        milesLength = round(value.Length * 0.000621371, 2)# convert meters to milles
        outStr += "," + str(milesLength) + "\n"
        outFile.write(outStr)    

    lockCSV.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='osm-stat')
    parser.add_argument("-inputfile")
    parser.add_argument("-url")
    parser.add_argument("-overpass")
    parser.add_argument("-history")
    parser.add_argument("-country")
    parser.add_argument("-pushCSV")
    parser.add_argument("-weeksCount")
    parser.add_argument("-db")
    args = parser.parse_args(sys.argv[1:])


    if args.weeksCount != "" and args.weeksCount != None:
        countOfWeeks = int(args.weeksCount)

    if args.country != "" and args.country != None:
        countryNames = []
        countryNames.append(str(args.country))

    if args.pushCSV != "" and args.pushCSV != None:
        StatDatabase.WriteCSVToDatabase(args.pushCSV)
        sys.exit(0)

    _lockCSV = multiprocessing.Lock()

    
    print "Count of weeks", countOfWeeks


    for countryName in countryNames:
        print "=============================="
        print "Start collect data for country : " + countryName
        print "=============================="

        bbox = GDALWorker.GetQueryBox(shpBoundFilename, countryName)
        print "Query box:", bbox
        #to test only:
        #bbox = {"s": "17.8951", "w": "-72.2948", "n": "18.2313", "e": "-70.9827"}


        outFilename = "output-" + countryName + ".csv"
        outFile = open(outFilename, "w")
        outFile.write("Date,Country,Name,Count,Length\n")
        outFile.close()


        if args.overpass == "true":
            for i in range(0, countOfWeeks):
                strDate = updateDate.strftime("%Y-%m-%dT%H:%M:%SZ")
                print "Extract date :", strDate
                RunSinlge(strDate, "", _lockCSV, countryName)
                # go to next month
                updateDate = MoveToNextWeek(updateDate)    
        elif args.inputfile != None:
            strDate = OSMDateInfo.GetDateFromFile(args.inputfile)    
            RunSinlge(strDate, "", _lockCSV, args)
        elif args.url != None:
            strDate = OSMDateInfo.GetDateFromUrl(args.url)
            RunSinlge(strDate, "", _lockCSV, args, countryName)
        elif args.history != None:
            # first clip and convert file
            if args.history.startswith("http://"):
                print "Start convert OSM data from history url: " + args.history
                fOutConvertName = OSMConverter.ConvertUrl(bbox, args.history, countryName)
            else:
                print "Start convert OSM data from history file: " + args.history
                fOutConvertName = OSMConverter.ConvertFile(bbox, args.history, countryName)

            # replace argument
            args.history = fOutConvertName

            enableThreading = (countOfWeeks >= 3);
            threadCount = 8
            threads = []

            for i in range(0, countOfWeeks):
                strDate = updateDate.strftime("%Y-%m-%dT%H:%M:%SZ")
                print "Extract date :", strDate
                if enableThreading:
                    postfix = str(len(threads) + 1)
                    th = multiprocessing.Process(target=RunSinlge, args=(strDate, postfix, _lockCSV, args, countryName))
                    th.start()
                    threads.append(th)
                else:
                    RunSinlge(strDate, "", _lockCSV, args, countryName)

                if len(threads) >= threadCount:
                    for th in threads:
                        th.join()
                    threads = []

                # go to next month  
                updateDate = MoveToNextWeek(updateDate)

            # wait latest threads
            if len(threads) > 0:
                 for th in threads:
                     th.join()
        else:
            raise "Not supported arguments"

        #print "Write to database"
        if args.db == None or args.db == "true":
            StatDatabase.WriteCSVToDatabase(outFilename)

        print "Done country : " + str(countryName)


    print "Done success"