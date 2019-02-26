#!/usr/bin/env python3

import csv
import json
import sys

from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

from aes import decrypt_file
from daco_client import DacoClient
from daco_user import User
from ego_client import EgoClient
from format_errors import err_msg
from report import create as create_report
from slack import Reporter as SlackReporter


def read_config(name="config/default.conf"):
    with open(name) as f:
        conf = json.load(f)
    return conf


def csv_to_dict(data):
    text = data.decode()
    csv_reader = csv.DictReader(text.splitlines())
    return [(u['openid'], u['user name']) for u in csv_reader]


def users_with_access_to(data):
    return {u[0] for u in data}


def is_member(members, candidate):
    return candidate in members


def daco_users(daco, cloud_members):
    return [User(email, name, True, email in cloud_members)
            for email, name in daco]


def invalid_users(cloud, daco_members):
    return [User(email, name, False, True)
            for email, name in cloud
            if email not in daco_members]


def get_users(daco, cloud):
    cloud_members = users_with_access_to(cloud)
    daco_members = users_with_access_to(daco)

    d = daco_users(daco, cloud_members)
    i = invalid_users(cloud, daco_members)

    return d + i


def send_report(issues):
    for issue in issues:
        print(issue)


def get_oauth_authenticated_client(base_url, client_id, client_secret):
    auth = HTTPBasicAuth(client_id, client_secret)
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    oauth.fetch_token(token_url=base_url + '/oauth/token', auth=auth)
    return oauth


def init(config):
    key = config['aes']['key']
    iv = config['aes']['iv']

    client_id = config['client']['client_id']
    client_secret = config['client']['client_secret']
    base_url = config['client']['base_url']
    daco_policies = set(config['client']['daco_policies'])
    cloud_policies = set(config['client']['cloud_policies'])

    rest_client = get_oauth_authenticated_client(base_url, client_id, client_secret)
    ego_client = EgoClient(base_url, daco_policies,
                           cloud_policies, rest_client)

    daco = csv_to_dict(decrypt_file(config['daco_file'], key, iv))
    cloud = csv_to_dict(decrypt_file(config['cloud_file'], key, iv))

    users = get_users(daco, cloud)
    daco_client = DacoClient(users, ego_client)

    return daco_client


def scream(msg, e):
    print(f"*** Failed to send report: {err_msg(msg, e)} ***")
    print(f"Sending a more reliable report somewhere else???")


def main(_program_name, *args):
    try:
        if args:
            config = read_config(args[0])
        else:
            config = read_config()
    except FileNotFoundError as f:
        scream(f"Can't read configuration file '{f.filename}'", f)
        exit(2)  # ENOENT (No such file or directory)
    except Exception as e:
        scream("Can't get configuration for daco2ego!", e)
        exit(2)

    try:
        slack_client = SlackReporter(config['slack']['url'])
    except Exception as e:
        scream("Can't get slack client to report errors!", e)
        exit(6)  # ENXIO (No such device or address)

    try:
        daco_client = init(config)
    except KeyError as e:
        issues = ["Daco2Ego configuration file error: missing entry for " + str(e) ]
        counts, errors = {}, issues
        ran = False
    except Exception as e:
        # Scenario 5 (Start-up failed)
        issues = ["DACO client init error:" + str(type(e)) + '(' + str(e)+ ')']
        counts, errors = {}, issues
        ran = False
    else:
        # Scenarios 1,2,3,4,6
        try:
            issues = daco_client.update_ego()
            counts, errors = daco_client.get_summary()
            ran = True
        except Exception as e:
            issues = [err_msg("Run failed", e)]
            counts, errors = {}, issues
            ran = False

    try:
        send_report(issues)
        report = create_report(counts, errors, ran)
        slack_client.send(report)
    except Exception as e:
        scream("Can't send out report", e)


if __name__ == "__main__":
    main(*sys.argv)
