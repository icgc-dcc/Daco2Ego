#!/usr/bin/env python3
import json
import sys
import gzip
import csv
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from daco_client import DacoClient

aes_bitsize=128
aes_blocksize=aes_bitsize / 8
aes_mode = AES.MODE_CBC

def read_config(name="config/default.conf"):
    with open(name) as f:
         conf = json.load(f)
    return conf

def read_gzip(name):
    with gzip.open(name, 'rb') as f:
         data=f.read()
    return data

def decrypt(data, key, iv):
    aes = AES.new(key, aes_mode, iv)
    return unpad(aes.decrypt(data), aes_blocksize)

def users(data):
    csvreader = csv.DictReader(data.splitlines())
    return { u['openid']: u for u in csvreader}

# AES doesnt specify how to pad variable length keys or initialization
# vectors.
# However, openSSL pads the key or value with trailing \0 bytes, so we
# do that, too, since we have to decrypt from openSSL.
def hexpad(hex_string,size):
    padding = size - int(len(hex_string)/2)
    return bytes.fromhex(hex_string + ("00" * padding))

def decrypt_file(aes_file, key, iv):
  return decrypt(bytes(read_gzip(aes_file)),
                 hexpad(key, aes_blocksize),
                 hexpad(iv, aes_blocksize))

def update_ego(ego, daco, cloud):
    """ Handle scenarios 1-4 wiki specification at
        https://wiki.oicr.on.ca/display/DCCSOFT/DACO2EGO

        Scenario 6 (error handling) is also handled implictly by all
        calls to our ego client, which traps and logs all exceptions.

        ego: A DacoClient object that can communicate with an ego server
        daco: A dictionary of user_ids mapped to the dictionary of CSV keys
              read from our file. Each users in the dictionary should have
              daco access. (user name,openid,email,csa)
        cloud:  A dictionary that of the same sort as above, for users
                who should have cloud access.

        returns: A list of issues encountered while handling the users
    """
    # get the set of daco and cloud ids
    daco_users =  daco.keys()
    cloud_users = cloud.keys()

    # Users who have cloud access but not daco are invalid users
    invalid_users = cloud_users - daco_users

    # Any user who is not invalid is valid
    valid_daco  = daco_users - invalid_users
    valid_cloud = cloud_users - invalid_users

    try:
        ego_users = ego.get_daco_users()
    except Exception as e:
        # scenario 6 (ego failure)
        return [ "Can't get user list from ego:" + str(e) ]

    # Handle scenario 4 (User has cloud access, but not daco access)
    for user in invalid_users:
        ego.revoke_all(user, "user in csa file but not in base DACO file")

    # scenarios 1 & 2
    for user in valid_daco:
        grant_cloud = user in valid_cloud
        if user not in ego_users:
            # Scenario 1
            details=ego.create_user(user, daco[user])
            ego_users[user] = details
        # scenario 2
        ego.ensure_access(user, grant_cloud)

    for user in ego_users:
        if user not in valid_daco:
            ego.revoke_all(user, "user not in daco list")
        elif user not in valid_cloud:
            ego.revoke_cloud(user)
    return ego.report_issues()

def send_report(issues):
    print(f"Daco2Ego report\nWe found these issues: {issues}")

def init(args):
    if args:
        config = read_config(args[0])
    else:
        config = read_config()

    client = DacoClient(config['client'])

    print("Getting daco users")
    key = config['aes']['key']
    iv  = config['aes']['iv']

    daco_users = users(decrypt_file(config['daco_file'], key, iv))
    cloud_users = users(decrypt_file(config['cloud_file'], key, iv))

    return client, daco_users, cloud_users

def main(_program_name, *args):
    issues = []

    try:
        (client, daco_users, cloud_users) = init(args)
    except Exception as e:
        # Scenario 5
        print(str(e))
        issues.append(str(e))
    else:
        # Scenarios 1,2,3,4,6
        update_ego(client, daco_users, cloud_users)
        issues = client.report_issues()

    send_report(issues)

if __name__ == "__main__":
   main(*sys.argv)
