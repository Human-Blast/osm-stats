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
import OSMConvertStat
import OSMConverter
import StatDatabase


#
# Application parameters:
#

# Parameters of date region
updateDate = datetime.date.today()
countOfWeeks = 1

# boundary of countries in shape format
shpBoundFilename = "./CountriesBounds/countries.shp"

highwayTypes = ["motorway", "secondary", 
                "secondary_link", "primary", "primary_link", 
                "tertiary", "residential", "unclassified",
                "road", "path", "service",
                "living_street", "track", "raceway"]
# End of applications parameters

def MoveToNextWeek(sourcedate):
        d = sourcedate - datetime.timedelta(days=7)
        return d

def RunSinlge(strDate, postfix, lockCSV, args, countryName, historyfilename):

    lockCSV.acquire()
    date = datetime.datetime.strptime(strDate, "%Y-%m-%dT%H:%M:%SZ")
    csvDateStr = date.strftime("%d %B %Y")
    print csvDateStr
    lockCSV.release()

    filenames = []
    res = {}


    # first download OSM data
    if args.overpass == "true":
        # download by Overpass_API
        print "Start download OSM data 'Overpass_API' "
        filenames = OsmDataProvider.GetOverpassOSMData(bbox, strDate, postfix)
    elif args.url != None:
        print "Start download OSM data 'url' " + args.url
        fName = OSMConverter.ConvertUrl(bbox, args.url, postfix)
        filenames.append(fName)

        print "Start calculate statistic..."
        res = GDALWorker.GetStatistic(filenames, highwayTypes, shpBoundFilename, countryName)
    elif args.inputfile != None:
        print "Parse OSM data 'inputfile' " + args.inputfile        
        spatPoly = GDALWorker.CreatePolyFile(shpBoundFilename, countryName)
        fName = OSMConverter.ConvertFile(spatPoly, args.inputfile, postfix, True)
        filenames.append(fName)

        print "Start calculate statistic..."
        res = GDALWorker.GetStatistic(filenames, highwayTypes, shpBoundFilename, countryName)
    elif args.history != None:
        lockCSV.acquire()
        print "Start extract OSM data from history file: " + historyfilename
        lockCSV.release()
        
        res = OSMConvertStat.GetStatistic(historyfilename, strDate, highwayTypes, postfix)
    else:
        raise "not supported"


    lockCSV.acquire()
    

    print "Write to CSV..."
    outFile = open("output-" + countryName + ".csv", "a")
    countryShortName = GDALWorker.GetShortCountryName(shpBoundFilename, countryName)
    for key, value in res.iteritems():
        outStr = csvDateStr
        outStr += "," + countryShortName
        outStr += "," + key
        outStr += "," + str(value.Count)
        milesLength = round(value.Length, 2)
        outStr += "," + str(milesLength) + "\n"
        outFile.write(outStr)    

    lockCSV.release()

def ConvertFile(countryName, filename, postfix, spatPoly , usePbf):
    # first clip and convert file
    if filename.startswith("http://"):
        print "Start convert OSM data from history url: " + filename
        fOutConvertName = OSMConverter.ConvertUrl(spatPoly, filename, postfix, True)
    else:
        print "Start convert OSM data from history file: " + filename
        fOutConvertName = OSMConverter.ConvertFile(spatPoly, filename, postfix, True)

if __name__ == '__main__':

    startTime = datetime.datetime.now()

    parser = argparse.ArgumentParser(prog='osm-stat')
    parser.add_argument("-inputfile")
    parser.add_argument("-url")
    parser.add_argument("-overpass")
    parser.add_argument("-history")
    parser.add_argument("-country")
    parser.add_argument("-pushCSV")
    parser.add_argument("-weeksCount")
    parser.add_argument("-dumpDatabase")
    parser.add_argument("-removeFromDatabase")
    parser.add_argument("-year")
    parser.add_argument("-dumpCountry")
    parser.add_argument("-db")
    parser.add_argument("-extractsReady")
    parser.add_argument("-date")
    parser.add_argument("-world")
    args = parser.parse_args(sys.argv[1:])

    if args.date != None:
        updateDate = datetime.datetime.strptime(args.date, "%Y.%m.%d").date()

    countryNames = GDALWorker.GetCountryNames(shpBoundFilename)


    if args.weeksCount != "" and args.weeksCount != None:
        countOfWeeks = int(args.weeksCount)

    if args.country != "" and args.country != None:
        countryNames = []
        countryNames.append(str(args.country))

    if args.world != None:
        StatDatabase.UpdateWorldStatistic(args.year)
        sys.exit(0)


    if args.pushCSV != "" and args.pushCSV != None:
        StatDatabase.WriteCSVToDatabase([args.pushCSV])
        sys.exit(0)

    if args.removeFromDatabase != "" and args.removeFromDatabase != None:
        if args.country == "" or args.country == None:
            raise "Country name not set"
        countryShortName = GDALWorker.GetShortCountryName(shpBoundFilename, args.country)
        print "Start remove country : " + countryShortName
        StatDatabase.RemoveFromDatabase(countryShortName, args.year)
        sys.exit(0)

    if args.dumpDatabase != "" and args.dumpDatabase != None:
        StatDatabase.DumptToCSV()
        sys.exit(0)

    if args.dumpCountry != "" and args.dumpCountry != None:
        if args.country == "" or args.country == None:
            raise "Country name not set"
        print "Start extract " + args.country + " OSM data from file: " + args.dumpCountry
        spatPoly = GDALWorker.CreatePolyFile(shpBoundFilename, args.country)
        print "Query box:", bbox
        fOutConvertName = OSMConverter.ConvertFile(spatPoly, args.dumpCountry, "", True)
        print "Dump success : " + fOutConvertName
        sys.exit(0)


    _lockCSV = multiprocessing.Lock()

    
    print "Count of weeks", countOfWeeks

    # Extract data for countries
    historyConvertFiles = {}
    if args.history != None and args.history != "":
        threadCount = 8
        threads = []

        for countryName in countryNames:
            postfix = str(countryName)
            fOutConvertName = "convert" + str(postfix) + ".pbf"

            if args.extractsReady == None:
                spatPoly = GDALWorker.CreatePolyFile(shpBoundFilename, countryName)

                th = multiprocessing.Process(target=ConvertFile, args=(countryName, args.history, postfix, spatPoly, True))
                th.start()
                threads.append(th)
            
            if len(threads) >= threadCount:
                for th in threads:
                    th.join()
                    if th.exitcode != 0:
                        raise "Convert process failed"
                    threads = []

            historyConvertFiles[countryName] = fOutConvertName

        # wait latest threads
        if len(threads) > 0:
            for th in threads:
                th.join()
                if th.exitcode != 0:
                    raise "Convert process failed"
            threads = []

    if args.overpass == "true":
        for countryName in countryNames:
            for i in range(0, countOfWeeks):
                strDate = updateDate.strftime("%Y-%m-%dT%H:%M:%SZ")
                print "Extract date :", strDate
                RunSinlge(strDate, "", _lockCSV, countryName, "")
                # go to next month
                updateDate = MoveToNextWeek(updateDate)

    elif args.inputfile != None:
        for countryName in countryNames:
            strDate = OSMDateInfo.GetDateFromFile(args.inputfile)    
            RunSinlge(strDate, "", _lockCSV, args, countryName, "")

    elif args.url != None:
        for countryName in countryNames:
            strDate = OSMDateInfo.GetDateFromUrl(args.url)
            RunSinlge(strDate, "", _lockCSV, args, countryName, "")

    elif args.history != None:



        for i in range(0, countOfWeeks):
            
            # Create CSVs
            for countryName in countryNames:
                outFilename = "output-" + countryName + ".csv"
                outFile = open(outFilename, "w")
                outFile.write("Date,Country,Name,Count,Length\n")
                outFile.close()

            strDate = updateDate.strftime("%Y-%m-%dT%H:%M:%SZ")

            # go to next month
            updateDate = MoveToNextWeek(updateDate)

            print "=============================="
            print "Extract date :", strDate
            print "=============================="

            startTimeDate = datetime.datetime.now()

            enableThreading = (len(countryNames) >= 3)
            threadCount = 8
            threads = []

            for countryName in countryNames:
                print "Start collect data for country : " + countryName
                outFilename = "output-" + countryName + ".csv"

                fOutConvertName = historyConvertFiles[countryName]

                if enableThreading:
                    postfix = str(countryName)
                    th = multiprocessing.Process(target=RunSinlge, args=(strDate, postfix, _lockCSV, args, countryName, fOutConvertName))
                    th.start()
                    threads.append(th)
                else:
                    RunSinlge(strDate, "", _lockCSV, args, countryName, fOutConvertName)

                while len(threads) >= threadCount:
                    aliveThreads = []
                    for th in threads:
                        th.join(1)
                        
                        if th.is_alive():
                            aliveThreads.append(th)
                            continue

                        if th.exitcode != 0:
                            raise "Extract process failed"
                    threads = aliveThreads

            # wait latest threads
            if len(threads) > 0:
                for th in threads:
                    th.join()
                    if th.exitcode != 0:
                        raise "Extract process failed"

            print "Done date : " + str(strDate)
        
            executeTimeDate = datetime.datetime.now() - startTimeDate
            print "ExecuteTime Date (minutes):", round(executeTimeDate.seconds / 60)

            if args.db == "true":
                print "Write to database"
                outFilenames = []
                for countryName in countryNames:
                    outFilename = "output-" + countryName + ".csv"
                    if os.path.isfile(outFilename):
                        outFilenames.append(outFilename)
                    
                StatDatabase.WriteCSVToDatabase(outFilenames)


    executeTime = datetime.datetime.now() - startTime
    print "ExecuteTime(minutes):", round(executeTime.seconds / 60)

    print "Done success"