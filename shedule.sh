#!/usr/bin/env bash
#
FILE="/mnt/terabyte/data/history-latest.osm.pbf"
echo $FILE
#if [ -f $FILE ];then
# rm $FILE
#fi
echo "Download file"
cd /mnt/terabyte/data
#wget http://planet.openstreetmap.org/pbf/full-history/history-latest.osm.pbf
rsync -v rsync://planet.openstreetmap.org/planet/pbf/full-history/history-latest.osm.pbf
echo "Start collect statistic"
cd /mnt/terabyte/data/OSM-stats
python2.7 /mnt/terabyte/data/OSM-stats/OSMStat.py -threadCountExtract 8 -weeksCount 575 -db true -history $FILE
