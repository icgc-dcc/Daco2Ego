#!/bin/bash
. set_vars.sh
# Generate config file from environment variables
cat > config <<-EOT
{
  "client": {
    "base_url": "${EGO_URL}",
    "client_id": "${CLIENT_ID}",
    "client_secret": "${CLIENT_SECRET}",
    "daco_group": "${DACO_GROUP}",
    "cloud_group":"${CLOUD_GROUP}" 
  },
  "aes": {
    "key": "${AES_KEY}",
    "iv":  "${AES_IV}"
  },
  "slack": {
    "url": "${SLACK_URL}"
  },
  "daco_file": "${DACO_FILE}",
  "cloud_file": "${CLOUD_FILE}"
}
EOT
