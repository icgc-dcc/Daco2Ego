#!/usr/local/bin/python3
import json
import sys
import gzip
from Crypto.Cipher import AES

def read_config(name="config/default.conf"):
    with open(name) as f:
         conf = json.load(f)
    return conf

def read_gzip(file):
    with gzip.open(file, 'rb') as f:
         data=f.read()
    return data

def decrypt(data, key, iv): 
    aes = AES.new(key, AES.MODE_CBC, iv)
    return aes.decrypt(data)

def users(data):
    return set( data.split(",") )

def decrypt_file(aes_file, config):
    return decrypt(read_gzip(aes_file),config['key'],config['iv'])

def update_ego(ego, daco_users, cloud_users):
    issues = []
    invalid_users = cloud_users - daco_users 
    valid_daco  = daco_users - invalid_users
    valid_cloud = cloud_users - invalid_users

    for user in invalid_users:
        issues +=  f"User {user} in csa file but not in base DACO file"
        ego.revoke_all(user)

    for user in valid_daco:
        grant_cloud = user in valid_cloud
        issues += ego.ensure_access(user, grant_cloud) 
    
    try:
       daco_users= ego.get_daco_users()
    except Exception as e:
       issues.append(e)

    for user in daco_users:
        if user not in valid_daco:
           issues += ego.revoke_all(user)
        elif user not in valid_cloud:
           issues += ego.revoke_cloud(user) 
 
    return issues

def send_report(issues):
    print(f"Daco2Ego report\nWe found these issues: {issues}")

def init(args):
    if args:
        config = read_config(args[0])
    else:
        config = read_config()

    client = DacoClient(config['client'])

    daco_users = users(decrypt_file(config['daco_file'], config['aes']))
    cloud_users = users(decrypt_file(config['cloud_file'], config['aes']))

    return client, daco_users, cloud_users


def main(_program_name, args):
    issues = []

    try:
        (client, daco_users, cloud_users) = init(args)
    except Exception as e:
        issues.append(e)
    else:
        issues.append(update_ego(client, daco_users, cloud_users))

    send_report(issues)

class EgoClient(object):
    def __init__(self, base_url, mocks=None):
            if mocks is None:
                mocks = {}
            self.base_url = base_url
            self.mocks = mocks

    def _get(self, endpoint):
        print(f"Connecting to {endpoint}")
        return self.mocks[endpoint]

    def get_users(self):
        return self._get("getUsers")

    def create_user(self, user):
        return self._get(f"createUser&user={user}")

    def get_scopes(self, user):
        return self._get(f"get_scopes&user={user}")

    def add_scopes(self, user, scopes):
        return self._get(f"&user={user}&scopes={scopes}")

    def remove_scopes(self,user,scopes):
        return self._get(f"removeScopes&user={user}&scopes={scopes}")

    def add_access(self, user, scopes):
        return self._get(f"add_access&user={user}&scopes={scopes}")

class DacoClient(object):
   daco_scope   = {'portal.READ'}
   cloud_scopes = {'aws.READ','collab.READ' }

   def __init__(self, config):
       self.client=EgoClient(config['base_url'])
        
   def get_daco_users(self):
       """ Return all users with aws.READ, portal.READ, or collab.READ 
           policies.
       """
       return self.client.get_users()

   def revoke_all(self, user):
        self.client.remove_scopes(user, self.cloud_scopes | self.daco_scope)

   def revoke_cloud(self, user):
        self.client.remove_scopes(user, self.cloud_scopes)

   def ensure_access(self, user, grant_cloud):
       issues=[]
       desired_scopes = self.daco_scope
       if grant_cloud:
          desired_scopes += self.cloud_scopes
       try:
          existing_scopes = self.client.get_scopes(user)
       except IndexError:
          existing_scopes = []
          issues += self.client.create_user(user)
       issues += self.client.add_access(user,desired_scopes - existing_scopes)
       return issues


if __name__ == "__main__":
   main(*sys.argv)
