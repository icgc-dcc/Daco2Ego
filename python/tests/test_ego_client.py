import json

from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

from ego_client import EgoClient


def read_config(name="config/default.conf"):
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
    daco_policies = set(config['client']['daco_policies'])
    cloud_policies = set(config['client']['cloud_policies'])

    rest_client = get_oauth_authenticated_client(base_url, client_id, client_secret)
    ego_client = EgoClient(base_url, daco_policies,
                           cloud_policies, rest_client)

    return ego_client


def test_ego_client():
    client = init()
    user, name = "test@gmail.com", "Test User"

    if not client.user_exists(user):
        has_daco(client, user, False)
        has_cloud(client, user, False)

        u = client.create_user(user, name)
        print(u)

        users = client.get_daco_users()
        assert user in users

    exists(client, user, True)
    has_daco(client, user, False)
    has_cloud(client, user, False)

    client.grant_daco(user)
    exists(client, user, True)
    has_daco(client, user, True)
    has_cloud(client, user, False)

    client.grant_cloud(user)
    has_daco(client, user, True)
    has_cloud(client, user, True)

    client.revoke_cloud(user)
    has_daco(client, user, True)
    has_cloud(client, user, False)

    client.revoke_daco(user)
    has_daco(client, user, False)
    has_cloud(client, user, False)
    exists(client, user, True)


def exists(client, user, status):
    assert client.user_exists(user) == status


def has_daco(client, user, status):
    assert client.has_daco(user) == status


def has_cloud(client, user, status):
    assert client.has_cloud(user) == status
