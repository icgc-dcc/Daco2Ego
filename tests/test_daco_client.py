#!/usr/bin/env python
from collections import OrderedDict
from daco_client import DacoClient 
from format_errors import format_exception
from mock_ego_client import (MockEgoSuccess, MockEgoException,
                             MockEgoFailure, ex_name)

daco=OrderedDict({'a@ca': 'Person A', 'b@ca':'Person B',
                  'd@ca':'Person D','e@ca': 'Person E','f@ca':'Person F'})
cloud=OrderedDict({'b@ca': 'Person B','c@ca': 'Person C', 'f@ca':'Person F',
       'g@ca': 'Person G'})

ego = OrderedDict({'a@ca':(True, False),'b@ca':(True, True),
                   'e@ca':(True, False),'g@ca':(True, True),
                   'h@ca':(True, True), 'c@ca':(False, True)})

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
    assert invalid == ['c@ca','g@ca']

def test_valid_daco():
    d = DacoClient(daco, cloud, None)
    valid = d.daco_users
    assert valid == ['a@ca','b@ca','d@ca', 'e@ca', 'f@ca']

def test_valid_cloud():
    d = DacoClient(daco, cloud, None)
    valid = d.cloud_users
    assert valid == {'b@ca','f@ca'}

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
    users = d.fetch_ego_ids()
    assert users == ego.keys()

    assert e.get_calls() == {'get_daco_users': ['Called'] }

    # ensure we didn't log anything on success
    report = d.report_issues()
    assert report == []

def test_get_ego_users_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    users = d.fetch_ego_ids()

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
    user = 'person@gmail.com'
    e = MockEgoSuccess({user:(False, False)})
    d = DacoClient({}, {}, e)


    d.grant_daco(user)
    expected = f"Granted daco access to user '{user}'"
    report = d.report_issues()
    assert report == [expected]

    assert e.get_calls() == {'grant_daco': [user]}

def test_access_fail():
    user = 'person@gmail.com'
    e = MockEgoFailure({user:(False, False)})
    d = DacoClient({},{}, e)

    d.grant_daco(user)
    assert e.get_calls() == {'grant_daco': [user]}
    msg = f"Can't grant daco access to user '{user}'"
    expected = err_msg(msg, 'grant_daco', user)
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
    user = 'a@ca'

    has_daco = e.has_daco(user)
    has_cloud  = e.has_cloud(user)

    (has_daco, has_cloud) == ego[user]
    assert e.get_calls() == {'has_daco': [user], 'has_cloud':[user]}

    # don't report permissions lookup unless it fails
    report = d.report_issues()
    assert report == []

def test_has_daco_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    user = 'a@ca'
    msg = None

    try:
       e.has_daco(user)
    except MockEgoException as ex:
        msg = repr(ex)

    assert e.get_calls() == { 'has_daco': [user] }

    assert msg == f"MockEgoException('{ex_name('has_daco',user)}')"

def test_has_cloud_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    user = 'a@ca'
    msg = None

    try:
       e.has_cloud(user)
    except MockEgoException as ex:
        msg = repr(ex)

    assert e.get_calls() == { 'has_cloud': [user] }

    assert msg == f"MockEgoException('{ex_name('has_cloud',user)}')"


def test_ensure_access():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    user = 'a@ca'
    grant_cloud=True
    d.ensure_access(user, grant_cloud)

    expected = [f"Granted cloud access to user '{user}'" ]
    report = d.report_issues()
    assert report == expected

def test_ensure2():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    user = 'a@ca'
    grant_cloud=False
    d.ensure_access(user, grant_cloud)

    expected = []
    report = d.report_issues()
    assert report == expected

def test_ensure3():
    e = MockEgoFailure(ego)
    d = DacoClient({},{}, e)
    user = 'f@ca'
    grant_cloud=True

    d.ensure_access(user, grant_cloud)
    msg1 = f"Can't tell if user '{user}' has daco access"
    msg2 = f"MockEgoException(User '{user}' does not exist in ego)"
    err = f"Error: {msg1} -- {msg2}"
    missing =  f"KeyError({user})"

    expected = [err,
                f"Error: Can't grant daco access to user '{user}' -- "
                + missing,
                err,
                f"Error: Can't grant cloud access to user '{user}' -- "+
                f"MockEgoException(grant_cloud({user}))",
                ]

    report = d.report_issues()
    print(f"We got: {report}")

    assert report == expected

def test_allowed1():
    e=MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    # user a is already set up correctly in ego
    user='a@ca'
    d.grant_access_if_necessary(user)

    assert e.get_calls() == { 'user_exists': [user],
                              'has_daco': [user]
                            }
    report = d.report_issues()
    assert report == []

def test_allowed2():
    e=MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    user='b@ca'
    # user b is already in Ego. He should have access to DACO and to Cloud
    d.grant_access_if_necessary(user)
    assert e.get_calls() == {'user_exists': [user],
                             'has_daco': [user],
                             'has_cloud': [user]
                             }

    expected = []
    report = d.report_issues()

    assert report == expected

def test_allowed3():
    e=MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    # user f is not in Ego. He should have access to DACO, and cloud.
    user='f@ca'
    d.grant_access_if_necessary(user)
    assert e.get_calls() == {'user_exists': [user],
                             'create_user': [(user, daco[user])],
                             'grant_daco': [user],
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
    user='b@ca'
    # We shouldn't change or log anything
    d.revoke_access_if_necessary(user)

    assert e.get_calls() == {}

    report = d.report_issues()
    assert report == []

def test_denied2():
    e = MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    user='g@ca'
    # User g' should no longer have DACO or cloud.
    d.revoke_access_if_necessary(user)
    assert e.get_calls() == { 'has_daco':[user],
                              'revoke_access': [user] }

    # ensure we logged the revoked access
    reason = "user not in daco list"
    expected = f"Revoked all daco access for user '{user}':({reason})"
    report = d.report_issues()
    assert report == [expected]

def test_denied3():
    e = MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    user='e@ca'
    # User e should have  DACO, but not cloud.
    # We should check to see if he has cloud (he doesn't).

    # We don't need to revoke his access, so nothing should be in the log.
    d.revoke_access_if_necessary(user)

    assert e.get_calls() == { 'has_cloud': [user]}
    # ensure we logged the revoked access
    #expected = f"Revoked cloud access for user 'e'"
    report = d.report_issues()
    assert report == []


def test_update_ego():
    e = MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)

    d.update_ego()

    expected =[
        "Revoked all daco access for user 'c@ca':(user in csa file but not in "
        "DACO file)",
        "Revoked all daco access for user 'g@ca':(user in csa file but not in "
        "DACO file)",
        'Created account for user d@ca with name Person D',
        "Granted daco access to user 'd@ca'",
        'Created account for user f@ca with name Person F',
        "Granted daco access to user 'f@ca'",
        "Granted cloud access to user 'f@ca'",
        "Revoked all daco access for user 'h@ca':(user not in daco list)",
    ]
    report = d.report_issues()
    assert report == expected

    print(e.get_calls())

    assert e.get_calls() == {
        'create_user': [('d@ca', 'Person D'), ('f@ca', 'Person F')],
        'has_daco': ['c@ca','g@ca','a@ca', 'b@ca', 'd@ca', 'e@ca', 'f@ca',
                     'g@ca','h@ca','c@ca'],
        'has_cloud': ['c@ca','b@ca', 'f@ca','a@ca','e@ca','g@ca',
                      'c@ca','d@ca'],
        'get_daco_users': ['Called'],
        'user_exists': ['a@ca', 'b@ca','d@ca','e@ca','f@ca'],
        'grant_daco': ['d@ca', 'f@ca'],
        'grant_cloud': ['f@ca'],
        'revoke_access': ['c@ca', 'g@ca', 'h@ca'],
    }
