#!/usr/bin/env python
from daco2ego import csv_to_dict, get_users, read_config
from daco_user import User


def test_read_config():
    expected = {
        "client": {"base_url": "https://ego/v1/"},
        "aes": {"key": "a1a2a3a4a5a6a7a8a9aa", "iv": "b1b2b3b4b5b6b7b8b9bb"},
        "daco_file": "config/daco.csv",
        "cloud_file": "config/cloud.csv"
    }
    config = read_config("tests/test.conf")
    assert config == expected


def file_to_dict(name):
    with open("tests/" + name, "rb") as f:
        return csv_to_dict(f.read())


def test_users():
    expected = [
        User('wonderful@gmail.com', '&Aacute; wo&ntilde;derful user',
             True, False),
        User('a.random.guy.random@gmail.com', 'SOME RANDOM GUY',
             True, True),
        User('a.person@gmail.com', 'A Person', True, False),
        User('cloud_only@gmail.com', 'Cloudy Future', False, True)]

    daco = file_to_dict("daco.csv")
    cloud = file_to_dict("cloud.csv")
    users = get_users(daco, cloud)
    print(users)
    assert users == expected
