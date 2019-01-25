#!/usr/bin/env python3
import json
import sys
import gzip
import csv
from Crypto.Cipher import AES
from daco_client import DacoClient

def read_config(name="config/default.conf"):
    with open(name) as f:
         conf = json.load(f)
    return conf

def read_gzip(name):
    with gzip.open(name, 'rb') as f:
         data=f.read()
    return data

def read_file(name):
    with open(name,'r') as f:
        data=f.read()
    return data

def decrypt(data, key, iv):
    print(f"Creating data extractor with key={key}({len(key)}), init vector="
          f"{iv}({len(iv)})")
    aes = AES.new(key, AES.MODE_CBC, iv)
    print(f"Decrypting data of type: {type(data)}")
    return aes.decrypt(data)

def users(data):
    # decode url entities
    csvreader = csv.DictReader(data.splitlines())
    return { u['openid']: u for u in csvreader}

# create a byte string of length size bytes with value
# from the given hex string.
def hexpad(hex_string,size):
    return bytes.fromhex(hex_string.zfill(2*size))

# def decrypt_file(aes_file, config):
#   return decrypt(bytes(read_file(aes_file)),
#                  hexpad(config['key'], 16),
#                  hexpad(config['iv'], 16))# 16 bytes

def decrypt_file(aes_file, config):
    with open(aes_file, "rb") as f:
        data=f.read()
    return data


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
    #daco_users = users(decrypt_file(config['daco_file'], config['aes']))
    daco_users = users(read_file(config['daco_file']))
    print("Getting cloud users")
    # cloud_users = users(decrypt_file(config['cloud_file'], config['aes']))
    cloud_users = users(read_file(config['cloud_file']))

    return client, daco_users, cloud_users


def main(_program_name, *args):
    issues = []

    try:
        (client, daco_users, cloud_users) = init(args)
    except Exception as e:
        # Scenario 5
        issues.append(str(e))
    else:
        # Scenarios 1,2,3,4,6
        issues.append(update_ego(client, daco_users, cloud_users))

    send_report(issues)






if __name__ == "__main__":
   main(*sys.argv)
