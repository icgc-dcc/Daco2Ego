#!/usr/bin/env python
from daco2ego import daco_users_csv_to_list, read_config
from daco_user import User


def test_read_config():
    expected = {
        "client": {
            "base_url": "https://ego/v1/",
            "daco_group": "DACO-TEST",
            "cloud_group":"DACO-CLOUD-TEST"
        },
        "daco_v2_client": {
            "ego_url": "https://ego/v2/",
            "dac_api_url": "https://dac-api/v2/"
        }
    }
    config = read_config("tests/test.conf")
    assert config == expected


def file_to_dict(name):
    with open("tests/" + name, "r") as f:
        return daco_users_csv_to_list(f.read())


def test_users():
    expected = [
        User('dd@example.com','DDD LLL', True, True),
        User('betty_gmail@example.com','Betty White',True, True),
        User('blanche_d@example.com', 'Blanche Devereaux', True, True),
        User('sofia_gmail6@example.com', 'NewFirst Tester',True, True),
        User('edna_k@example.com', 'Edna Krabapple', True, True),
        User('gary_chalmers@example.com', 'Gary Chalmers', True, True )
    ]

    daco = file_to_dict("test_users.csv")
    print(daco)
    assert daco == expected
