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
                statItem.Week = int(date.strftime("%W"))
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


def WriteCSVToDatabase(filename):
    import psycopg2

    # Get statistic from CSV
    statCSV = GetStatisticFromFile(filename)
    statKeysCSV = {}
    for item in statCSV:
        key = str(item.Country) + str(item.Year) + str(item.Week) + str(item.Kind)
        statKeysCSV[key] = True


    conn = psycopg2.connect("postgres://xksrylseratnzb:MLlMNpKQXP-st8vNW3rj0JShmh@ec2-54-235-78-240.compute-1.amazonaws.com:5432/d8hhbphanhc0fd")
    cur = conn.cursor()    

    cur.execute("SELECT \"country_code\", \"year\", \"week\", \"kind\", \"count\", \"length\" from road_stats")
    rows = cur.fetchall()
    for row in rows:
        keyRow = str(row[0]) + str(row[1]) + str(row[2]) + str(row[3])
        if statKeysCSV.has_key(keyRow):
            # Delete previous record
            cur.execute("DELETE from road_stats WHERE country_code=%s AND year=%s AND week=%s AND kind=%s", [row[0], row[1], row[2], row[3]])
    # Pull new values
    for item in statCSV:
        cur.execute("INSERT INTO road_stats (\"country_code\", \"year\", \"week\", \"kind\", \"count\", \"length\") values(%s,%s,%s,%s,%s,%s)", [item.Country, item.Year, item.Week, item.Kind, item.Count, item.Length])

    conn.commit()
    cur.close()
    conn.close()