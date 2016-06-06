import sys
import os
import httplib
import datetime
import csv

databaseConnection = ""


class StaticsticRes:
    Country = ""
    Year = 0
    Week = 0
    Kind = ""
    Length = 0
    Count = 0


def GetStatisticFromFile(filename):
        res = []
        with open(filename, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|')
            isFirst = True
            for row in reader:
                if isFirst:
                    isFirst = False
                    continue#skip header
                statItem = StaticsticRes()

                dateStr = str(row[0])
                date = datetime.datetime.strptime(dateStr, "%d %B %Y").date()
                statItem.Year = date.year
                statItem.Week = date.isocalendar()[1];
                statItem.Country = str(row[1])
                statItem.Kind = str(row[2])
                statItem.Count = int(row[3])
                statItem.Length = float(row[4])

                res.append(statItem)

        return res

def RemoveFromDatabase(countryShortName, year):
    import psycopg2

    conn = psycopg2.connect("postgres://xksrylseratnzb:MLlMNpKQXP-st8vNW3rj0JShmh@ec2-54-235-78-240.compute-1.amazonaws.com:5432/d8hhbphanhc0fd")
    cur = conn.cursor()    

    if(countryShortName == "" or countryShortName == None):
        cur.execute("DELETE from road_stats WHERE year=%s", [year])
    else:
        if year != None and year != "":
            cur.execute("DELETE from road_stats WHERE country_code=%s AND year=%s", [countryShortName, year])
        else:
            cur.execute("DELETE from road_stats WHERE country_code=%s", [countryShortName])

    conn.commit()
    cur.close()
    conn.close()

def DumptToCSV():
    import psycopg2

    conn = psycopg2.connect("postgres://xksrylseratnzb:MLlMNpKQXP-st8vNW3rj0JShmh@ec2-54-235-78-240.compute-1.amazonaws.com:5432/d8hhbphanhc0fd")
    cur = conn.cursor()   
    
    cur.execute("SELECT \"country_code\", \"year\", \"week\", \"kind\", \"count\", \"length\" from road_stats")
    rows = cur.fetchall()
    with open("database_dump.csv", 'w') as outFile:
        for row in rows:
            outStr = ""
            for item in row:
                if(outStr != ""):
                    outStr += ","
                outStr += str(item)
            outStr += "\n"
            outFile.write(outStr)    

    cur.close()
    conn.close()

def WriteCSVToDatabase(filenames):
    import psycopg2
    conn = psycopg2.connect("postgres://xksrylseratnzb:MLlMNpKQXP-st8vNW3rj0JShmh@ec2-54-235-78-240.compute-1.amazonaws.com:5432/d8hhbphanhc0fd")
    cur = conn.cursor()    
    
    for filename in filenames:
        # Get statistic from CSV
        statCSV = GetStatisticFromFile(filename)

        print "Start push CSV to database : ", filename

        for item in statCSV:
             # Delete previous record
             cur.execute("DELETE from road_stats WHERE country_code=%s AND year=%s AND week=%s AND kind=%s", [item.Country, item.Year, item.Week, item.Kind])                    

        # Pull new values
        for item in statCSV:
            cur.execute("INSERT INTO road_stats (\"country_code\", \"year\", \"week\", \"kind\", \"count\", \"length\") values(%s,%s,%s,%s,%s,%s)", [item.Country, item.Year, item.Week, item.Kind, item.Count, item.Length])

    conn.commit()
    cur.close()
    conn.close()

    print "Push complete"

def UpdateWorldStatistic(year):
    import psycopg2

    print "Start update WORLD statistic"

    conn = psycopg2.connect("postgres://xksrylseratnzb:MLlMNpKQXP-st8vNW3rj0JShmh@ec2-54-235-78-240.compute-1.amazonaws.com:5432/d8hhbphanhc0fd")
    cur = conn.cursor()    

    # delete previous world data 
    cur.execute("DELETE from road_stats WHERE country_code=%s", ["world"])

    cur.execute("SELECT \"year\" from road_stats")
    rows = cur.fetchall()
    
    #if any(len(r) > 0 for r in rows) == False:
    #    return

    minYear = 0
    maxYear = 0

    if year != None:
        minYear = int(year)
        maxYear = int(year)
    else: 
        isInit = False
        for row in rows:
            year = int(row[0])
            if isInit == False:
                minYear = year
                maxYear = year
                isInit = True
                continue

            minYear = min(minYear, year)
            maxYear = max(maxYear, year)


    for year in range(minYear, maxYear + 1):
        print "Update statistic for year:", year
        for week in range(0, 55):
            cur.execute("SELECT \"kind\", \"count\", \"length\" from road_stats WHERE year=%s AND week=%s", [year, week])
            rows = cur.fetchall()
            if (len(rows) == 0):
                continue
            res = {}
            for row in rows:
                kind = row[0]
                if(res.has_key(kind) == False):
                    res[kind] = StaticsticRes()
                stat = res[kind]
                stat.Count += int(row[1])
                stat.Length += float(row[2])

            for key,item in res.iteritems():
                cur.execute("INSERT INTO road_stats (\"country_code\", \"year\", \"week\", \"kind\", \"count\", \"length\") values(%s,%s,%s,%s,%s,%s)", ["world", year, week, key, item.Count, item.Length])

    conn.commit()
    cur.close()
    conn.close()
