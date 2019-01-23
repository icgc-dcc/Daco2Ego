#!/usr/local/bin/python3
import json
import sys
def read_config(name="config/default.conf"):
    with open(name) as f:
         conf = json.load(f)
    return conf

def main(args):
    if args:
       config=read_config(args[0])
    else:
       config = read_config()
    print("Read config:", config)
    
if __name__ == "__main__":
   (program_name, *args) = sys.argv
   main(args)   
