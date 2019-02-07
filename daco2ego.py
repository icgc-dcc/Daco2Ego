#!/usr/bin/env python3
import json
from collections import OrderedDict
import sys
from aes import decrypt_file
from ego_client import EgoClient
from requests import Session
from user import User
from format_errors import err_msg
import csv

from daco_client import DacoClient

def read_config(name="config/default.conf"):
    with open(name) as f:
         conf = json.load(f)
    return conf

def csv_to_dict(data):
    text = data.decode()
    csvreader = csv.DictReader(text.splitlines())
    return [(u['openid'], u['user name']) for u in csvreader]

def users_with_access_to(data):
    return {u[0] for u in data}

def is_member(members, candidate):
    return candidate in members

def daco_users(daco, cloud_members):
    return [User(email,name,True, email in cloud_members)
                for email,name in daco]

def invalid_users(cloud, daco_members):
    return [User(email, name, False, True)
            for email,name in cloud
            if not email in daco_members ]

def get_users(daco, cloud):
    cloud_members = users_with_access_to(cloud)
    daco_members = users_with_access_to(daco)

    d = daco_users(daco, cloud_members)
    i = invalid_users(cloud, daco_members)

    return d + i

def send_report(issues):
    for issue in issues:
        print(issue) 

def init(args):
    if args:
        config = read_config(args[0])
    else:
        config = read_config()

    key = config['aes']['key']
    iv  = config['aes']['iv']

    auth_token = config['client']['auth_token']
    base_url   = config['client']['base_url']

    rest_client = Session()
    ego_client = EgoClient(base_url, auth_token, rest_client)

    daco = csv_to_dict(decrypt_file(config['daco_file'], key, iv))
    cloud = csv_to_dict(decrypt_file(config['cloud_file'], key, iv))

    users = get_users(daco, cloud)
    client = DacoClient(users, ego_client)

    return client

def scream(msg, e):
    print(f"*** Failure to send report {msg} -- {e} ***")
    print(f"Sending a more reliable report somewhere else???")

def main(_program_name, *args):
    try:
        daco_client = init(args)
    except IOError as e:
        # Scenario 5 (Start-up failed)
        issues = ["Initialization error:" + str(e)]
    else:
        # Scenarios 1,2,3,4,6
        try:
            issues = daco_client.update_ego()
        except Exception as e:
            issues = [err_msg("Unknown error",e)]
    
    try:
        send_report(issues)
    except Exception as e:
        scream("Can't send out report", e)

if __name__ == "__main__":
   main(*sys.argv)
