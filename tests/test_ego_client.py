#!/usr/bin/env python
from requests import Session
from ego_client import EgoClient
base_url="https://api.staging.cancercollaboratory.org"
auth_token = "Basic ZGFjbzJlZ286ZGFjbw=="
daco_policies = {"portal"}
cloud_policies = {"aws", "collab"}
rest_client = Session()
e=EgoClient(base_url, auth_token, daco_policies, cloud_policies, rest_client)