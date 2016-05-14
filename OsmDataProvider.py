import sys
import httplib
import urllib
import time
import string
import codecs

def DumpToFile(data):
    return

def GetResponse(overpassServerUrl, overpassPage, bbox, strDate):
        # specify we're sending parameters that are url encoded
        boxStr = bbox["s"] + "," + bbox["w"] + "," + bbox["n"] + "," + bbox["e"]
        data = "[date:\"" + strDate + "\"];"
        data += "(node(" + boxStr + ");way(" + boxStr + "););out;" 
        params = urllib.urlencode({'data': data})
        headers = {"Content-type": "application/x-www-form-urlencoded", 
                "Accept": "text/plain"}
        conn = httplib.HTTPConnection(overpassServerUrl)
        conn.request("POST", overpassPage, params, headers)
        response = conn.getresponse()
        return response

def GetOSMData(filename, overpassServerUrl, overpassPage, bbox, strDate):
        tryCounter = 0
        
        while(True):
            response = GetResponse(overpassServerUrl, overpassPage, bbox, strDate)
            print response.status, response.reason
            
            if response.status == 429: #Too Many Requests
                time.sleep(70) # delays for 70 seconds
                tryCounter += 1
                if tryCounter > 5:
                    raise Exception("Can't download data Too Many Requests")
                continue

            if response.status == 200:
                break
            raise Exception("Can't download data")

        print "Downloading data..."


        with codecs.open(filename, "w", "utf-8") as osmFile:
            fileLen = response.length
            chunckSize = 20000
            while(True):
                respData = response.read(chunckSize)
                if(respData == None or respData == ""):
                    break
                try:
                    respDataUnicode = unicode(respData, "utf-8", errors='replace')
                    osmFile.write(respDataUnicode)
                except:
                    print "Unexpected error:", sys.exc_info()[0]
                    raise
                osmFile.flush()

        return


