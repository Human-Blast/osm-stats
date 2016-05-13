import sys
import httplib
import urllib
import time

def DumpToFile(data):
    return

def GetResponse(overpassServerUrl, overpassPage, bbox, strDate):
        # specify we're sending parameters that are url encoded
        boxStr = bbox["s"] + "," + bbox["w"] + "," + bbox["n"] + "," + bbox["e"]
        data = "[date:\"" + strDate + "\"];";
        data += "(node(" + boxStr + ");way("  + boxStr + "););out;" 
        params = urllib.urlencode({'data': data})
        headers = {"Content-type": "application/x-www-form-urlencoded", 
                "Accept": "text/plain"}
        conn = httplib.HTTPConnection(overpassServerUrl)
        conn.request("POST", overpassPage, params, headers)
        response = conn.getresponse()
        return response

def GetOSMData(overpassServerUrl, overpassPage, bbox, strDate):
        tryCounter = 0
        
        while(True):
            response = GetResponse(overpassServerUrl, overpassPage, bbox, strDate)
            print response.status, response.reason
            
            if response.status == 429: #Too Many Requests
                time.sleep(20) # delays for 20 seconds
                tryCounter += 1
                if tryCounter > 5:
                    raise Exception("Can't download data Too Many Requests")
                continue

            if response.status == 200:
                break
            raise Exception("Can't download data")

        print "Downloading data..."

        filename = "source.osm"

        osmFile = open(filename, "w")
        
        fileLen = response.length
        chunckSize = 20000
        while(True):
            respData = response.read(chunckSize)
            if(respData == None or respData == ""):
                break
            osmFile.write(respData)

        osmFile.close()

        return filename


