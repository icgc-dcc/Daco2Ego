#!/bin/bash
echo "Content-type: text/plain"
echo

. /daco2ego/set_vars.sh
echo -n "Uploading..."
sed -e "s/
sed -e "/^$/,/^$/{/^$/d;p};d" | \
openssl enc -aes-128-cbc -nosalt -K $AES_KEY -iv $AES_IV 2>/dev/null | \
gzip -f > ${DACO_FILE}
echo "Done"
exit 0