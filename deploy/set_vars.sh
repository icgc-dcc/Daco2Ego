#!/bin/bash
# pull our secrets out the JSON file that init.sh creates and into environment variables 
CLIENT_ID=$(cat secrets | jq -r .data.CLIENT_ID) 
CLIENT_SECRET=$(cat secrets | jq -r .data.CLIENT_SECRET) 
AES_IV=$(cat secrets | jq -r .data.AES_IV) 
AES_KEY=$(cat secrets | jq -r .data.AES_KEY) 
SLACK_URL=$(cat secrets | jq -r .data.SLACK_URL)

export SERVER_PORT CLIENT_SECRET CLIENT_ID AES_KEY AES_IV SLACK_URL EGO_URL DACO_GROUP CLOUD_GROUP DACO_FILE CLOUD_FILE LOG_FILE
