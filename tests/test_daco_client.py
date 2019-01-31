#!/usr/bin/env python
from collections import OrderedDict
from daco_client import DacoClient, format_exception
from mock_ego_client import (MockEgoSuccess, MockEgoException,
                             MockEgoFailure, ex_name)

daco=OrderedDict({'a': 'Person A', 'b':'Person B', 'd':'Person D',
      'e': 'Person E','f':'Person F'})
cloud=OrderedDict({'b': 'Person B','c': 'Person C', 'f':'Person F',
       'g': 'Person G'})

ego = OrderedDict({'a':(True, False),'b':(True, True),'e':(True, False),
                'h':(True, True)})

def err_msg(msg, name, *args):
        ex = ex_name(name, *args)
        return f"Error: {msg} -- MockEgoException({ex})"

def test_log():
    d=DacoClient({},{},None)
    msg1="This is message one"
    msg2="This is message two"
    msg3="This is message three"
    assert d.report_issues() == []
    d.log(msg1)
    assert d.report_issues() == [msg1]
    d.log(msg2)
    assert d.report_issues() == [msg1, msg2]
    d.log(msg3)
    assert d.report_issues() == [msg1, msg2, msg3]

def test_err():
    d=DacoClient({},{},None)
    msg1="This is message1"
    msg2="This is message2"
    e=Exception(msg1)
    d.err(msg1,e)
    err = format_exception(e)
    assert d.report_issues() == [ f"Error: {msg1} -- {err}" ]
    d.log(msg2)
    assert d.report_issues() == [f"Error: {msg1} -- {err}", msg2]

def test_invalid():
    d=DacoClient(daco, cloud, None)
    invalid = d.invalid_users
    assert invalid == ['c','g']

def test_valid_daco():
    d = DacoClient(daco, cloud, None)
    valid = d.all_users
    assert valid == ['a','b','d', 'e', 'f']

def test_valid_cloud():
    d = DacoClient(daco, cloud, None)
    valid = d.cloud_users
    assert valid == ['b','f']

def test_user_name_success():
    user = "a.person@gmail.com"
    name = "A Person"
    daco1 = {user: name}

    d = DacoClient(daco1,{},None)
    assert d.get_user_name(user) == name
    assert d.report_issues() == []

def test_name_fail():
    user = "a.person@gmail.com"
    d = DacoClient({},{}, None)
    assert d.get_user_name(user) is None
    expected = f"Error: Can't get name for user {user} -- KeyError({user})"
    assert d.report_issues() == [expected]

def test_create_user_success():
    e=MockEgoSuccess(ego)
    d=DacoClient({}, {}, e)
    user = 'a.random.guy.random@gmail.com'
    name = "A Person"

    # ensure we called our ego interface correctly
    d.create_user(user, name)
    assert e.get_calls() == { 'create_user' : [ (user, name) ] }

    # ensure that our user creation was logged
    expected = f"Created account for user {user} with name {name}"
    report = d.report_issues()
    assert report == [ expected ]

def test_user_fail():
    e=MockEgoFailure(ego)
    d=DacoClient({}, {}, e)
    user = 'a.random.guy.random@gmail.com'
    name = "A Person"

    d.create_user(user, name)
    assert e.get_calls() == {'create_user': [(user, name)]}

    report = d.report_issues()
    msg = f"Can't create user '{user}'"
    expected =  err_msg(msg, 'create_user', user, name)

    assert report== [expected]

def test_get_ego_users():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    users = d.get_ego_users()
    assert users == ego.keys()

    assert e.get_calls() == {'get_daco_users': ['Called'] }

    # ensure we didn't log anything on success
    report = d.report_issues()
    assert report == []

def test_get_ego_users_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    users = d.get_ego_users()

    assert users == {}
    assert e.get_calls() == {'get_daco_users': ['Called']}

    msg = "Can't get list of daco users from ego"
    expected = err_msg(msg, 'get_daco_users')

    report = d.report_issues()
    assert report == [expected]

def test_revoke_access():
    e=MockEgoSuccess(ego)
    d=DacoClient({},{}, e)
    user='person@gmail.com'
    reason="Account Consistency Check Failed"

    d.revoke_access(user, reason)
    assert e.get_calls() == {'revoke_access': [user]}

    expected = f"Revoked all daco access for user '{user}':({reason})"
    report = d.report_issues()
    assert report == [expected]

def test_revoke_access_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    user = 'person@gmail.com'
    reason = "Account Consistency Check Failed"

    d.revoke_access(user, reason)
    assert e.get_calls() == { 'revoke_access': [user] }
    msg = f"Can't revoke daco access for user '{user}'"
    expected = err_msg(msg,'revoke_access',user)

    report = d.report_issues()
    assert report == [expected]

def test_revoke_cloud():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    user = 'person@gmail.com'

    d.revoke_cloud(user)
    assert e.get_calls() == { 'revoke_cloud': [user] }

    expected = f"Revoked cloud access for user '{user}'"
    report = d.report_issues()
    assert report == [expected]

def test_revoke_cloud_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    user = 'person@gmail.com'

    d.revoke_cloud(user)
    assert e.get_calls() == { 'revoke_cloud': [user]}
    msg = f"Can't revoke cloud access for user '{user}'"

    expected = err_msg(msg, 'revoke_cloud', user)
    report = d.report_issues()
    assert report == [expected]

def test_grant_access():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    user = 'person@gmail.com'

    d.grant_access(user)
    assert e.get_calls() == {'grant_access': [user]}

    expected = f"Granted daco access to user '{user}'"
    report = d.report_issues()
    assert report == [expected]

def test_access_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({},{}, e)
    user = 'person@gmail.com'

    d.grant_access(user)
    assert e.get_calls() == {'grant_access': [user]}
    msg = f"Can't grant daco access to user '{user}'"
    expected = err_msg(msg, 'grant_access', user)
    report = d.report_issues()
    assert report == [expected]

def test_grant_cloud():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    user = 'person@gmail.com'

    d.grant_cloud(user)
    assert e.get_calls() == {'grant_cloud': [user]}

    expected = f"Granted cloud access to user '{user}'"
    report = d.report_issues()
    assert report == [expected]

def test_grant_cloud_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    user = 'person@gmail.com'

    d.grant_cloud(user)
    assert e.get_calls() == {'grant_cloud': [user]}

    msg = f"Can't grant cloud access to user '{user}'"
    expected = err_msg(msg, 'grant_cloud', user)
    report = d.report_issues()
    assert report == [expected]


def test_get_daco_access():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    user = 'a'

    assert d.get_daco_access(user) == ego[user]
    assert e.get_calls() == {'get_daco_access': [user]}

    # don't report permissions lookup unless it fails
    report = d.report_issues()
    assert report == []

def test_daco_access_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    user = 'a'
    msg = None

    try:
       d.get_daco_access(user)
    except MockEgoException as ex:
        msg = repr(ex)

    assert e.get_calls() == { 'get_daco_access': [user] }

    assert msg == f"MockEgoException('{ex_name('get_daco_access',user)}')"

def test_ensure_access():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    user = 'a'
    grant_cloud=True
    d.ensure_access(user, grant_cloud)

    expected = [f"User '{user}' already has daco access",
                f"Granted cloud access to user '{user}'" ]
    report = d.report_issues()
    assert report == expected

def test_ensure2():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    user = 'a'
    grant_cloud=False
    d.ensure_access(user, grant_cloud)

    expected = [f"User '{user}' already has daco access"]
    report = d.report_issues()
    assert report == expected

def test_ensure3():
    e = MockEgoSuccess(ego)
    d = DacoClient({},{}, e)
    user = 'f'
    grant_cloud=True

    d.ensure_access(user, grant_cloud)
    msg1 = f"Can't get ego settings for user '{user}'"
    msg2 = f"MockEgoException(User '{user}' does not exist in ego)"


    expected = [f"Error: {msg1} -- {msg2}"]

    report = d.report_issues()
    assert report == expected

def test_allowed1():
    e=MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    # user a is already set up correctly in ego
    user='a'
    d.handle_access_allowed(user)

    assert e.get_calls() == { 'user_exists': [user],
                              'get_daco_access': [user]
                            }
    expected = f"User '{user}' already has daco access"
    report = d.report_issues()
    assert report == [expected]

def test_allowed2():
    e=MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    user='b'
    # user b is already in Ego. He should have access to DACO and to Cloud
    d.handle_access_allowed(user)
    assert e.get_calls() == {'user_exists': [user],
                             'get_daco_access': [user]
                             }

    expected = [f"User '{user}' already has daco access",
                f"User '{user}' already has cloud access"]
    report = d.report_issues()

    assert report == expected

def test_allowed3():
    e=MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    # user f is not in Ego. He should have access to DACO, and cloud.
    user='f'
    d.handle_access_allowed(user)
    assert e.get_calls() == {'user_exists': [user],
                             'get_daco_access': [user],
                             'create_user': [(user, daco[user])],
                             'grant_access': [user],
                             'grant_cloud': [user]
                             }

    expected = [f"Created account for user {user} with name {daco[user]}",
                f"Granted daco access to user '{user}'",
                f"Granted cloud access to user '{user}'"
                ]
    report = d.report_issues()
    assert report == expected

def test_denied1():
    e = MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    # user 'b' is in Ego, and should still keep EGO and Cloud
    user='b'
    # We shouldn't change or log anything
    d.handle_access_denied(user)

    assert e.get_calls() == {}

    report = d.report_issues()
    assert report == []

def test_denied2():
    e = MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    user='g'
    # user 'g' is in Ego, but no longer has DACO or cloud.
    d.handle_access_denied(user)
    assert e.get_calls() == { 'revoke_access': [user] }

    # ensure we logged the revoked access
    reason = "user not in daco list"
    expected = f"Revoked all daco access for user '{user}':({reason})"
    report = d.report_issues()
    assert report == [expected]

def test_denied3():
    e = MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    user='e'
    # user 'e' is in Ego, and has DACO, but not cloud.
    d.handle_access_denied('e')

    assert e.get_calls() == {'revoke_cloud': [user]}
    # ensure we logged the revoked access
    expected = f"Revoked cloud access for user 'e'"
    report = d.report_issues()
    assert report == [expected]


def test_update_ego():
    e = MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)

    d.update_ego()

    expected =[
        "Revoked all daco access for user 'c':(user in csa file but not in DACO file)",
        "Revoked all daco access for user 'g':(user in csa file but not in DACO file)",
        "User 'a' already has daco access",
        "User 'b' already has daco access",
        "User 'b' already has cloud access",
        'Created account for user d with name Person D',
        "Granted daco access to user 'd'",
        "User 'e' already has daco access",
        'Created account for user f with name Person F',
        "Granted daco access to user 'f'",
        "Granted cloud access to user 'f'",
        "Revoked cloud access for user 'a'",
        "Revoked cloud access for user 'e'",
        "Revoked all daco access for user 'h':(user not in daco list)",
        "Revoked cloud access for user 'd'"]
    report = d.report_issues()
    assert report == expected


    assert e.get_calls() == {
        'create_user': [('d', 'Person D'), ('f', 'Person F')],
        'get_daco_access': ['a', 'b', 'd', 'e', 'f'],
        'get_daco_users': ['Called'],
        'user_exists': ['a', 'b','d','e','f'],
        'grant_access': ['d', 'f'],
        'grant_cloud': ['f'],
        'revoke_access': ['c', 'g', 'h'],
        'revoke_cloud': ['a', 'e', 'd']
    }