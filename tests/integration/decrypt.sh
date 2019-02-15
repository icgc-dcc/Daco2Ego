#!/bin/sh
file=$1
unzip=${file%.gz}
decrypt=${unzip%.enc}.decrypt
#echo "file=$file, unzip=$unzip, decrypt=$decrypt"

KEY=${2:-a1a2a3a4a5a6a7a8a9aa}
IV=${3:-b1b2b3b4b5b6b7b8b9bb}

gunzip $file | openssl enc -aes-128-cbc -d -in $unzip -nosalt -nopad -K $KEY -iv $IV > $decrypt
