#!/bin/bash
file=${DACO_FILE}
touch $file
chown nobody:nobody $file

while true;do
   inotifyd ./run.sh ${file}:c 
done
