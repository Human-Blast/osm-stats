import sys
import httplib
import datetime
import calendar
import time
import OsmDataProvider
import GDALWorker

# application parameters
overpassServerUrl = "overpass-api.de"
overpassPage = "/api/interpreter"
# boundary of Haiti in shape format
shpBoundFilename = "./CountriesBounds/HTI_adm0.shp"
highwayTypes = ["motorway", "motorway_link", "secondary", 
                "secondary_link", "primary", "primary_link", 
                "tertiary", "residential", "unclassified",
                "road", "path", "service",
                "living_street", "track", "raceway"
                ]

bbox = GDALWorker.GetQueryBox(shpBoundFilename)
print "Query box:", bbox
#to test only:
#bbox = {"s": "17.8951", "w": "-72.2948", "n": "18.2313", "e": "-70.9827"}

def AddMonths(sourcedate,months):
         month = sourcedate.month - 1 + months
         year = int(sourcedate.year + month / 12 )
         month = month % 12 + 1
         day = min(sourcedate.day,calendar.monthrange(year,month)[1])
         return datetime.date(year,month,day)


updateDate = datetime.date(2016, 01, 01)

outFile = open("output.csv", "w")
outFile.write("Date,Name,Count,Length\n")
outFile.close()

for i in range(1, 5):
    strDate = updateDate.strftime("%Y-%m-%dT%H:%M:%SZ")
    print "Update time :", strDate

    filename = "source.osm"

    # first download OSM data by Overpass_API
    print "Start download OSM data 'Overpass_API' "
    OsmDataProvider.GetOSMData(filename, overpassServerUrl, overpassPage, bbox, strDate)

    print "Start calculate lengths"
    res = GDALWorker.GetStatistic(filename, highwayTypes, shpBoundFilename)

    print "Write to CSV..."

    outFile = open("output.csv", "a")
    
    for key, value in res.iteritems():
        outStr = updateDate.strftime("%d %B %Y")
        outStr += "," + key
        outStr += "," + str(value.Count)
        milesLength = round(value.Length * 0.000621371, 2)# convert meters to milles
        outStr += "," + str(milesLength) + "\n"
        outFile.write(outStr)
    
    outFile.close()

    # go to next month
    updateDate = AddMonths(updateDate, 1)    

print "Done success"