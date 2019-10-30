#!/bin/bash
#set -x
: ${SERVER_PORT:=8081}
: ${CLIENT_SECRET:="shhh!"}
: ${CLIENT_ID:="daco2ego"}
: ${AES_KEY:="a1a2a3a4a5a6a7a8a9aa"}
: ${AES_IV:="b1b2b3b4b5b6b7b8b9bb"}
: ${SLACK_URL:="http://localhost:${SERVER_PORT}/report.cgi"}
: ${EGO_URL:="https://ego.dev.argo.cancercollaboratory.org/api"}
: ${DACO_GROUP:="DACO"}
: ${CLOUD_GROUP:="CLOUD"}
: ${DACO_FILE:="/daco2ego/files/team.csv.enc.gz"}
: ${CLOUD_FILE:="/daco2ego/files/team.csv.enc.gz"}
: ${LOG_FILE:=daco2ego.log}

if [ "${VAULT_ENABLED}" = "true" ];then
    # fetch the jwt that vault gave us
    jwt=$(cat ${VAULT_TOKEN_FILE})

    # use the jwt auth token to get a vault authorization token for our role 
    vault_token=$(curl ${VAULT_URL}/v1${VAULT_LOGIN_PATH} --data "{\"jwt\": \"${jwt}\", \"role\": \"${VAULT_ROLE}\"}" | jq -r .auth.client_token)

    # use our authorization token to get our secrets
    curl --header "X-Vault-Token: $vault_token" --LIST ${VAULT_URL}/v1/${VAULT_SECRETS_PATH%/} > secrets

    # pull our secrets out the JSON file and into environment variables 
    CLIENT_ID=$(cat secrets | jq -r .data.CLIENT_ID) 
    CLIENT_SECRET=$(cat secrets | jq -r .data.CLIENT_SECRET) 
    AES_IV=$(cat secrets | jq -r .data.AES_IV) 
    AES_KEY=$(cat secrets | jq -r .data.AES_KEY) 
    SLACK_URL=$(cat secrets | jq -r .data.SLACK_URL)
fi
export SERVER_PORT CLIENT_SECRET CLIENT_ID AES_KEY AES_IV SLACK_URL EGO_URL DACO_GROUP CLOUD_GROUP DACO_FILE CLOUD_FILE LOG_FILE
