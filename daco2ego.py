#!/usr/bin/env python3
import json
from collections import OrderedDict
import sys
from aes import decrypt_file
from ego_client import EgoClient
import csv

from daco_client import DacoClient

def read_config(name="config/default.conf"):
    with open(name) as f:
         conf = json.load(f)
    return conf

def users(data):
    text = data.decode()
    csvreader = csv.DictReader(text.splitlines())
    return OrderedDict([ (u['openid'], u['user name']) for u in csvreader])

def send_report(issues):
    print(f"Daco2Ego report\nWe found these issues: {issues}")

def init(args):
    if args:
        config = read_config(args[0])
    else:
        config = read_config()

    key = config['aes']['key']
    iv  = config['aes']['iv']

    daco_users = users(decrypt_file(config['daco_file'], key, iv))
    cloud_users = users(decrypt_file(config['cloud_file'], key, iv))
    auth_token = config['client']['auth_token']
    base_url   = config['client']['base_url']

    ego_client = EgoClient(config[''], base_url, auth_token)
    client = DacoClient(daco_users, cloud_users, ego_client)

    return client

def main(_program_name, *args):
    issues = []

    try:
        daco_client = init(args)
    except Exception as e:
        # Scenario 5 (Start-up failed)
        issues.append("Initialization error:" + str(e))
    else:
        # Scenarios 1,2,3,4,6
        issues = daco_client.update_ego()
    send_report(issues)

if __name__ == "__main__":
   main(*sys.argv)
