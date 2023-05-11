import json

from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

from ego_client import EgoClient


def read_config(name="tests/test_ego.conf"):
    with open(name) as f:
        conf = json.load(f)
    return conf


def get_oauth_authenticated_client(base_url, client_id, client_secret):
    auth = HTTPBasicAuth(client_id, client_secret)
    client = BackendApplicationClient(client_id=client_id)
    oauth = OAuth2Session(client=client)
    oauth.fetch_token(token_url=base_url + '/oauth/token', auth=auth)
    return oauth


def init():
    config = read_config()
    client_id = config['client']['client_id']
    client_secret = config['client']['client_secret']
    base_url = config['client']['base_url']

    rest_client = get_oauth_authenticated_client(base_url, client_id, client_secret)
    ego_client = EgoClient(base_url, rest_client)

    return ego_client


def test_ego_client():
    client = init()
    config = read_config()
    daco_group_name = config['client']['daco_group']
    cloud_group_name = config['client']['cloud_group']
    user, name = "test@gmail.com", "Test User"

    if not client.user_exists(user):
        has_daco(client, user, False)
        has_cloud(client, user, False)

        u = client.create_user(user, name)
        print(u)

        assert client.user_exists(user)

    exists(client, user, True)
    has_daco(client, user, False)
    has_cloud(client, user, False)

    client.add(daco_group_name, [user])
    exists(client, user, True)
    has_daco(client, user, True)
    has_cloud(client, user, False)

    client.add(cloud_group_name,[user])
    has_daco(client, user, True)
    has_cloud(client, user, True)

    client.remove(cloud_group_name,[user])
    has_daco(client, user, True)
    has_cloud(client, user, False)

    client.remove(daco_group_name,[user])
    has_daco(client, user, False)
    has_cloud(client, user, False)
    exists(client, user, True)

def exists(client, user, status):
    assert client.user_exists(user) == status

def has_daco(client, user, status):
    config = read_config()
    daco_group_name = config['client']['daco_group']
    assert client.is_member(daco_group_name, user) == status

def has_cloud(client, user, status):
    config = read_config()
    cloud_group_name = config['client']['cloud_group']
    assert client.is_member(cloud_group_name, user) == status
