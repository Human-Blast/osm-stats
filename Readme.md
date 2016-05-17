A OSM-stats is phyton script that collect statistic about ways in OSM data.

To apply spatial filter by country script use predefined polygon from shapefile in folder "CountriesBounds".

You can configure desired highway types in list "highwayTypes" in file "OSMStat.py".

//////////////////////// Options ///////////////////

-inputfile : parse OSM planet file

Example:  -inputfile "planet.osm.bz2" 

-url : download and parse OSM file

Example: -url "http://download.gisgraphy.com/openstreetmap/pbf/AD.tar.bz2"

-overpass: use OverpassAPI to download data  This API allowed get "Historic dumps" of OSM data. More info about  "Overpass_API"

Example:  -overpass true

//////////////////////// Linux ///////////////////

To run script you will need install next packages:

1. 

sudo apt-get install python2.7 python2.7-dev

2. 

sudo apt-get install gdal-bin


3.

sudo apt-get install python-gdal


//////////////////////// Windows  ///////////////////

To run script on Windows platform you will need run "run.bat" Output wil be in the file "output.csv".

//////////////////////// Output  ///////////////////

Output CSV file contains next fields:

"Date" - is date of "Historic dump"

"Name" - is type of "highway" in OSM data

"Count" - is count of ways

"Length" - is summary length of ways in milles
