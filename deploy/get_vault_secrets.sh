#!/bin/bash
#set -x
# fetch the jwt that vault gave us
jwt=$(cat ${VAULT_TOKEN_FILE})

# use the jwt auth token to get a vault authorization token for our role 
vault_token=$(curl ${VAULT_URL}/v1${VAULT_LOGIN_PATH} --data "{\"jwt\": \"${jwt}\", \"role\": \"${VAULT_ROLE}\"}" | jq -r .auth.client_token)

# use our authorization token to get our secrets
curl --header "X-Vault-Token: $vault_token" --LIST ${VAULT_URL}/v1/${VAULT_SECRETS_PATH%/} 
