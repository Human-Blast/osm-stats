# OSM-stats
A OSM-stats is python script that collect statistic about ways in OSM data. It's output is at http://osm-stats.stevecoast.com/

To apply spatial filter by country script use predefined polygon from shapefile in folder "CountriesBounds".

You can configure desired highway types in list "highwayTypes" in file "OSMStat.py".

## Options

-history : parse full-history OSM file

Example:  

```sh
python2.7 OSMStat.py -history "history-latest.osm.pbf" 
```

```sh
python2.7 OSMStat.py -history "http://planet.openstreetmap.org/pbf/full-history/history-latest.osm.pbf"
```

-inputfile : parse OSM planet file

Example:  

```sh
python2.7 OSMStat.py -inputfile "planet.osm.bz2" 
```

-country : set name of country

-pushCSV: push csv file to database

-weeksCount: latest weeks count

-db: wirte result to database

-dumpDatabase: dump database to CSV

-world: update statistic for world in database

-overpass: use OverpassAPI to download data  This API allowed get "Historic dumps" of OSM data. More info about  "Overpass_API"

Example:  

```sh
python2.7 OSMStat.py -overpass true
```

## Linux 

You will need install next dependence packages:

```sh
sudo apt-get install python2.7 python2.7-dev gdal-bin python-gdal python-psycopg2
```

To run script you will run command:
```sh
python2.7 OSMStat.py -inputfile "planetfile.osm.bz"
```


## Windows 

To run script on Windows platform you will need run "run.bat" Output wil be in the file "output.csv".

## Output

Output CSV file contains next fields:

- "Date" - date of "Historic dump"
- "Country" - country code like "fr", "ht", "ru"
- "Name" - kind of OSM data 
- "Count" - count of ways
- "Length" - summary length of ways in milles
