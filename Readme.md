A OSM-stats is phyton script that collect statistic about ways in OSM data.

OSM-stats use the "Overpass_API" to download OSM data. This API allowed get "Historic dumps" of OSM data. More info about  "Overpass_API" :

http://wiki.openstreetmap.org/wiki/Overpass_API/versions

http://wiki.openstreetmap.org/wiki/Overpass_API

To apply spatial filter by country script use predefined polygon from shapefile in folder "CountriesBounds".

To run script on Windows platform you will need run "run.bat" Output wil be in the file "output.csv".

Output CSV file contains next fields:

"Date" - is date of "Historic dump"

"Name" - is type of "highway" in OSM data

"Count" - is count of ways

"Length" - is summary length of ways in milles

You can configure desired highway types in list "highwayTypes" in file "OSMStat.py".
You can configure desired range of dates by variables "updateDate" and "countOfMonth"
