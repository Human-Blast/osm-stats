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
updateDate = datetime.date.today();
countOfWeeks = 1

# boundary of countries in shape format
shpBoundFilename = "./CountriesBounds/countries.shp"

highwayTypes = ["motorway", "secondary", 
                "secondary_link", "primary", "primary_link", 
                "tertiary", "residential", "unclassified",
                "road", "path", "service",
                "living_street", "track", "raceway"
                ]
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
        print "Start extract OSM data from history file: " + historyfilename
        lockCSV.release()
        
        fName = OSMHistory.ExtractHistory(historyfilename, strDate, postfix)
        filenames.append(fName)
    else:
        raise "not supported"


    lockCSV.acquire()
    
    print "Start calculate statistic..."
    res = GDALWorker.GetStatistic(filenames, highwayTypes, shpBoundFilename, countryName)

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

def ConvertFile(countryName, filename, postfix, spatPoly , usePbf):
        # first clip and convert file
        if filename.startswith("http://"):
            print "Start convert OSM data from history url: " + filename
            fOutConvertName = OSMConverter.ConvertUrl(spatPoly, filename, postfix, True)
        else:
            print "Start convert OSM data from history file: " + filename
            fOutConvertName = OSMConverter.ConvertFile(spatPoly, filename, postfix, True)

if __name__ == '__main__':
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
    args = parser.parse_args(sys.argv[1:])

    countryNames = GDALWorker.GetCountryNames(shpBoundFilename)


    if args.weeksCount != "" and args.weeksCount != None:
        countOfWeeks = int(args.weeksCount)

    if args.country != "" and args.country != None:
        countryNames = []
        countryNames.append(str(args.country))

    if args.pushCSV != "" and args.pushCSV != None:
        StatDatabase.WriteCSVToDatabase(args.pushCSV)
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
            spatPoly = GDALWorker.CreatePolyFile(shpBoundFilename, countryName)

            postfix = str(len(threads) + 1)
            fOutConvertName = "convert" + str(postfix) + ".pbf"
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

    for countryName in countryNames:
        print "=============================="
        print "Start collect data for country : " + countryName
        print "=============================="


        outFilename = "output-" + countryName + ".csv"
        outFile = open(outFilename, "w")
        outFile.write("Date,Country,Name,Count,Length\n")
        outFile.close()

        if args.overpass == "true":
            for i in range(0, countOfWeeks):
                strDate = updateDate.strftime("%Y-%m-%dT%H:%M:%SZ")
                print "Extract date :", strDate
                RunSinlge(strDate, "", _lockCSV, countryName, "")
                # go to next month
                updateDate = MoveToNextWeek(updateDate)    
        elif args.inputfile != None:
            strDate = OSMDateInfo.GetDateFromFile(args.inputfile)    
            RunSinlge(strDate, "", _lockCSV, args, "", "")
        elif args.url != None:
            strDate = OSMDateInfo.GetDateFromUrl(args.url)
            RunSinlge(strDate, "", _lockCSV, args, countryName, "")
        elif args.history != None:
            fOutConvertName = historyConvertFiles[countryName]

            enableThreading = (countOfWeeks >= 3);
            threadCount = 8
            threads = []

            for i in range(0, countOfWeeks):
                strDate = updateDate.strftime("%Y-%m-%dT%H:%M:%SZ")
                print "Extract date :", strDate
                if enableThreading:
                    postfix = str(len(threads) + 1)
                    th = multiprocessing.Process(target=RunSinlge, args=(strDate, postfix, _lockCSV, args, countryName, fOutConvertName))
                    th.start()
                    threads.append(th)
                else:
                    RunSinlge(strDate, "", _lockCSV, args, countryName, fOutConvertName)

                if len(threads) >= threadCount:
                    for th in threads:
                        th.join()
                        if th.exitcode != 0:
                            raise "Extract process failed"
                    threads = []

                # go to next month  
                updateDate = MoveToNextWeek(updateDate)

            # wait latest threads
            if len(threads) > 0:
                 for th in threads:
                     th.join()
                     if th.exitcode != 0:
                          raise "Extract process failed"
        else:
            raise "Not supported arguments"

        #print "Write to database"
        if args.db == "true":
            StatDatabase.WriteCSVToDatabase(outFilename)

        print "Done country : " + str(countryName)


    print "Done success"