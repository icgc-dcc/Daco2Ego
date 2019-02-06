#!/usr/bin/env python
from daco2ego import read_config, get_users

def test_read_config():
    expected= {
        "client": { "base_url": "https://ego/v1/" },
        "aes": {"key":"a1a2a3a4a5a6a7a8a9aa", "iv": "b1b2b3b4b5b6b7b8b9bb" },
        "daco_file":  "config/daco.csv",
        "cloud_file": "config/cloud.csv"
    }
    config=read_config("test.conf")
    assert config == expected

def test_users():
    expected = {'a.person@gmail.com': 'A Person',
                'a.random.guy.random@gmail.com': 'SOME RANDOM GUY',
                'wonderful@gmail.com': '&Aacute; wo&ntilde;derful user'
                }
    with open("test_data","rb") as f:
         data = f.read()
    assert data is not None 
    actual = get_users(data)
    assert actual == expected
