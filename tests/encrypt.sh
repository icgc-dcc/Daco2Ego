#!/bin/sh
file=$1
KEY=${2:-a1a2a3a4a5a6a7a8a9aa}
IV=${3:-b1b2b3b4b5b6b7b8b9bb}
openssl enc -aes-128-cbc -in $file -nosalt -K $KEY -iv $IV | gzip -f > ${file}.enc.gz
