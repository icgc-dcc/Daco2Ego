#!/usr/bin/env python3

import csv
import json
import sys
import logging

from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

from daco_client import DacoClient
from daco_user import User
from ego_client import EgoClient
from format_errors import err_msg
from report import create as create_report
from slack import Reporter as SlackReporter
from daco_v2_ego_client import DacoV2EgoClient


def read_config(name="config/default.conf"):
    with open(name) as f:
        conf = json.load(f)
    return conf

def daco_users_csv_to_list(data):
    ret_list = []
    reader = csv.DictReader(data.splitlines())

    for user in reader:
        print(f'DACO 2 user:', user)
        openid = user['OPENID'].lower()
        user_name = user['USER NAME']
        ret_list.append(User(openid,user_name,True,True))

    return ret_list

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


def send_report(issues, summary):
    print(summary)
    print("* Detailed Issues Log *")
    for issue in issues:
        print(issue)
    print("* End of report *")


def get_oauth_authenticated_client(base_url, client_id, client_secret):
    auth = HTTPBasicAuth(client_id, client_secret)
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    oauth.fetch_token(token_url=base_url + '/oauth/token', auth=auth)
    return oauth


def init(config):
    client_id = config['client']['client_id']
    client_secret = config['client']['client_secret']
    base_url = config['client']['base_url']

    daco_v2_ego_url = config['daco_v2_client']['ego_url']
    daco_v2_client_id = config['daco_v2_client']['client_id']
    daco_v2_client_secret = config['daco_v2_client']['client_secret']
    dac_api_url = config['daco_v2_client']['dac_api_url']

    rest_client = get_oauth_authenticated_client(base_url, client_id, client_secret)
    ego_client = EgoClient(base_url, rest_client,  # Want to create a factory for new oauth clients
                           lambda: get_oauth_authenticated_client(base_url, client_id, client_secret))

    # create second rest and ego client to access permissions for dac-api in argo ego
    daco_v2_rest_client = get_oauth_authenticated_client(daco_v2_ego_url, daco_v2_client_id, daco_v2_client_secret)
    daco_v2_ego_client = DacoV2EgoClient(daco_v2_ego_url, daco_v2_rest_client, dac_api_url,  # Want to create a factory for new oauth clients
                            lambda: get_oauth_authenticated_client(daco_v2_ego_url, daco_v2_client_id, daco_v2_client_secret))

    approved_users = daco_v2_ego_client.download_approved_users()
    approved_users_list = daco_users_csv_to_list(approved_users)

    daco_group = config['client']['daco_group']
    cloud_group = config['client']['cloud_group']
    daco_client = DacoClient(daco_group, cloud_group, approved_users_list, ego_client)

    logging.info('Daco Client Initialized.');
    return daco_client


def logError(msg, e):
    print(f"*** Failed to send report: {err_msg(msg, e)} ***")


def main(_program_name, *args):
    config = None
    slack_client = None
    try:
        if args:
            config = read_config(args[0])
        else:
            config = read_config()
    except FileNotFoundError as f:
        logError(f"Can't read configuration file '{f.filename}'", f)
        exit(2)  # ENOENT (No such file or directory)
    except Exception as e:
        logError("Can't get configuration for daco2ego!", e)
        exit(2)

    logging.info('Configuration Loaded.')

    try:
        slack_client = SlackReporter(config['slack']['url'])
    except Exception as e:
        logError("Can't get slack client to report errors!", e)
        exit(6)  # ENXIO (No such device or address)

    logging.info('Slack webhook configured.')

    try:
        daco_client = init(config)
    except KeyError as e:
        issues = ["Daco2Ego configuration file error: missing entry for " + str(e)]
        counts, errors = {}, issues
        ran = False
    except Exception as e:
        # Scenario 5 (Start-up failed)
        issues = ["DACO client init error:" + str(type(e)) + '(' + str(e) + ')']
        counts, errors = {}, issues
        ran = False
    else:
        # Scenarios 1,2,3,4,6
        try:
            logging.info("Starting Ego Update...")
            issues = daco_client.update_ego()
            counts, errors = daco_client.get_summary()
            ran = True
        except Exception as e:
            issues = [err_msg("Run failed", e)]
            counts, errors = {}, issues
            ran = False

    try:
        summary = create_report(counts, errors, ran)
        send_report(issues, summary)
        slack_client.send(summary)

    except Exception as e:
        logError("Can't send out report", e)


if __name__ == "__main__":
    main(*sys.argv)
