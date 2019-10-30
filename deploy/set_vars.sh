#!/bin/bash
# pull our secrets out the JSON file that init.sh creates and into environment variables 
FILE="/daco2ego/secrets"
CLIENT_ID=$(cat $FILE | jq -r .data.CLIENT_ID) 
CLIENT_SECRET=$(cat $FILE | jq -r .data.CLIENT_SECRET) 
AES_IV=$(cat $FILE | jq -r .data.AES_IV) 
AES_KEY=$(cat $FILE | jq -r .data.AES_KEY) 
SLACK_URL=$(cat $FILE | jq -r .data.SLACK_URL)

export SERVER_PORT CLIENT_SECRET CLIENT_ID AES_KEY AES_IV SLACK_URL EGO_URL DACO_GROUP CLOUD_GROUP DACO_FILE CLOUD_FILE LOG_FILE
