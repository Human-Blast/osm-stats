import sys
import httplib
import datetime
import calendar
import time
import argparse
import OsmDataProvider
import GDALWorker
import OSMDateInfo


#
# Application parameters:
#

# Parameters of date region
updateDate = datetime.date(2015, 05, 01)
countOfMonth = 12

# boundary of countries in shape format
shpBoundFilename = "./CountriesBounds/countries.shp"
countryName = "Greenland"

highwayTypes = ["motorway", "secondary", 
                "secondary_link", "primary", "primary_link", 
                "tertiary", "residential", "unclassified",
                "road", "path", "service",
                "living_street", "track", "raceway"
                ]

# End of applications parameters

bbox = GDALWorker.GetQueryBox(shpBoundFilename, countryName)
print "Query box:", bbox
#to test only:
#bbox = {"s": "17.8951", "w": "-72.2948", "n": "18.2313", "e": "-70.9827"}

def AddMonths(sourcedate,months):
         month = sourcedate.month - 1 + months
         year = int(sourcedate.year + month / 12 )
         month = month % 12 + 1
         day = min(sourcedate.day,calendar.monthrange(year,month)[1])
         return datetime.date(year,month,day)

parser = argparse.ArgumentParser(prog='osm-stat')
parser.add_argument("-inputfile")
parser.add_argument("-url")
parser.add_argument("-overpass")
args = parser.parse_args(sys.argv[1:])


def RunSinlge(strDate):
    filenames = []

    # first download OSM data 
    if args.overpass == "true":
        # download by Overpass_API
        print "Start download OSM data 'Overpass_API' "
        filenames = OsmDataProvider.GetOverpassOSMData(bbox, strDate)
    elif args.url != None:
        print "Start download OSM data 'url' " + args.url
        fName = OsmDataProvider.GetUrlOSMData(bbox, args.url)
        filenames.append(fName)
    elif args.inputfile != None:
        print "Parse OSM data 'inputfile' " + args.inputfile
        fName = OsmDataProvider.GetFileOSMData(bbox, args.inputfile)
        filenames.append(fName)
    else:
        raise "not supported"

    print "Start calculate statistic..."
    res = GDALWorker.GetStatistic(filenames, highwayTypes, shpBoundFilename, countryName)

    print "Write to CSV..."

    outFile = open("output.csv", "a")
    
    for key, value in res.iteritems():
        outStr = strDate
        outStr += "," + key
        outStr += "," + str(value.Count)
        milesLength = round(value.Length * 0.000621371, 2)# convert meters to milles
        outStr += "," + str(milesLength) + "\n"
        outFile.write(outStr)
    
    

outFile = open("output.csv", "w")
outFile.write("Date,Name,Count,Length\n")
outFile.close()


if args.overpass == "true":
    for i in range(0, countOfMonth):
        strDate = updateDate.strftime("%Y-%m-%dT%H:%M:%SZ")
        print "Update time :", strDate

        RunSinlge(strDate)

        # go to next month
        updateDate = AddMonths(updateDate, 1)    
elif args.inputfile != None:
    strDate = OSMDateInfo.GetDateFromFile(args.inputfile)
    RunSinlge(strDate)
elif args.url != None:
    strDate = OSMDateInfo.GetDateFromUrl(args.url)
    RunSinlge(strDate)

else:
    raise "not supported arguments"


outFile.close()


print "Done success"