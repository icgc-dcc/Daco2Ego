#!/usr/bin/env python
from daco_client import DacoClient
from mock_ego_client import MockEgoSuccess, MockEgoException, MockEgoFailure

daco={'a': 'Person A', 'b':'Person B', 'd':'Person D',
      'e': 'Person E','f':'Person F'}
cloud={'b': 'Person B','c': 'Person C', 'f':'Person F',
       'g': 'Person G'}
ego = {'a','b','e','h'}

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

def test_invalid():
    d=DacoClient(daco, cloud, None)
    invalid = d.invalid_users()
    assert invalid == {'c','g'}

def test_valid_daco():
    d = DacoClient(daco, cloud, None)
    valid = d.valid_daco_users()
    assert valid == {'a','b','d', 'e', 'f'}

def test_valid_cloud():
    d = DacoClient(daco, cloud, None)
    valid = d.valid_cloud_users()
    assert valid == {'b','f'}

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
    expected = f"Error: Can't get name for user {user} -- KeyError('{user}')"
    assert d.report_issues() == [expected]

def test_create_user_success():
    e=MockEgoSuccess(ego)
    d=DacoClient({}, {}, e)
    user = 'a.random.guy.random@gmail.com'
    name = "A Person"

    d.create_user(user, name)

    # ensure that we called e.create_user(user, name)
    # and nothing else
    assert e.log_create_user == [ (user, name) ]
    assert e.log_ensure_access == []
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 0

    # ensure that our user creation was logged
    expected = f"Created account for user {user} with name {name}"
    report = d.report_issues()
    assert report == [ expected ]

def test_user_fail():
    e=MockEgoFailure(ego)
    d=DacoClient({}, {}, e)
    user = 'a.random.guy.random@gmail.com'
    name = "A Person"
    fail = f"Error: Can't create user '{user}' -- " \
        f"MockEgoException('create_user(user={user}, name={name})')"

    d.create_user(user, name)
    # ensure that we called e.create_user(user, name)
    # and nothing else
    assert e.log_create_user == [(user, name)]
    assert e.log_ensure_access == []
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 0

    # ensure that we logged the failure correctly
    report = d.report_issues()
    assert report== [fail]

def get_ego_users():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    users = d.get_ego_users()
    assert users == ego

    # ensure we called ego.get_daco_users(), and
    # nothing else
    assert e.log_create_user == []
    assert e.log_ensure_access == []
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 1

    # ensure we didn't log anything on success
    report = d.report_issues()
    assert report == []

def get_ego_users_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    users = d.get_ego_users()
    assert users == []

    # ensure we called e.get_daco_users(), and
    # nothing else
    assert e.log_create_user == []
    assert e.log_ensure_access == []
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 1

    expected = f"Error: Can't get list of daco users from ego: -- " \
               f"MockEgoException('get_daco_users()')"
    # ensure we logged the connection failure
    report = d.report_issues()
    assert report == [expected]

def test_revoke_access():
    e=MockEgoSuccess(ego)
    d=DacoClient({},{}, e)
    user='person@gmail.com'
    reason="Account Consistency Check Failed"

    d.revoke_access(user, reason)
    # ensure that we called e.revoke_access(user)
    # and nothing else
    assert e.log_create_user == []
    assert e.log_ensure_access == []
    assert e.log_revoke_access == [user]
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 0

    # ensure we logged the revoked access
    expected = f"Revoked all daco access for user '{user}':({reason})"
    report = d.report_issues()
    assert report == [expected]

def test_revoke_access_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    user = 'person@gmail.com'
    reason = "Account Consistency Check Failed"

    d.revoke_access(user, reason)
    # ensure that we called e.revoke_access(user)
    # and nothing else
    assert e.log_create_user == []
    assert e.log_ensure_access == []
    assert e.log_revoke_access == [user]
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 0

    # ensure we logged the revoked access
    expected = f"Error: Can't revoke daco access for user '{user}' -- " \
               f"MockEgoException('revoke_access(user={user})')"
    report = d.report_issues()
    assert report == [expected]

def test_revoke_cloud():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    user = 'person@gmail.com'

    d.revoke_cloud(user)
    # ensure that we called ego.client.create_user(user, name)
    # and nothing else
    assert e.log_create_user == []
    assert e.log_ensure_access == []
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == [user]
    assert e.called_get_daco_users == 0

    # ensure we logged the revoked access
    expected = f"Revoked cloud access for user '{user}'"
    report = d.report_issues()
    assert report == [expected]

def test_revoke_cloud_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    user = 'person@gmail.com'

    d.revoke_cloud(user)
    # ensure that we called ego.client.create_user(user, name)
    # and nothing else
    assert e.log_create_user == []
    assert e.log_ensure_access == []
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == [user]
    assert e.called_get_daco_users == 0

    # ensure we logged the revoked access
    expected = f"Error: Can't revoke cloud access for user '{user}' -- " \
               f"MockEgoException('revoke_cloud(user={user})')"
    report = d.report_issues()
    assert report == [expected]

def test_ensure_access():
    e = MockEgoSuccess(ego)
    d = DacoClient({}, {}, e)
    user = 'person@gmail.com'
    grant_cloud=True
    d.ensure_access(user, grant_cloud)
    # ensure that we called ego.client.create_user(user, name)
    # and nothing else
    assert e.log_create_user == []
    assert e.log_ensure_access == [(user, grant_cloud)]
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 0

    # ensure we logged the access
    expected = f"Ensured user '{user}' has daco access (cloud={grant_cloud})"
    report = d.report_issues()
    assert report == [expected]

def test_ensure_access_fail():
    e = MockEgoFailure(ego)
    d = DacoClient({}, {}, e)
    user = 'person@gmail.com'
    grant_cloud=False

    d.ensure_access(user, grant_cloud)
    # ensure that we called ego.client.create_user(user, name)
    # and nothing else
    assert e.log_create_user == []
    assert e.log_ensure_access == [(user, grant_cloud)]
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 0

    # ensure we logged our failure
    expected = f"Error: Can't ensure access for user '{user}'" \
               f"(cloud={grant_cloud}) -- " \
               f"MockEgoException('ensure_access(user={user}, " \
               f"grant={grant_cloud})')"
    report = d.report_issues()
    assert report == [expected]

def test_allowed1():
    e=MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    # user a is already in Ego. He should have access to DACO, but not cloud.
    d.handle_access_allowed('a')

    assert e.log_create_user == []
    assert e.log_ensure_access == [('a',False)]
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 1

    expected = f"Ensured user 'a' has daco access (cloud=False)"
    report = d.report_issues()
    assert report == [expected]

def test_allowed2():
    e=MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    # user b is already in Ego. He should have access to DACO and to Cloud
    d.handle_access_allowed('b')

    assert e.log_create_user == []
    assert e.log_ensure_access == [('b',True)]
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 1

    expected = f"Ensured user 'b' has daco access (cloud=True)"
    report = d.report_issues()

    assert report == [expected]

def test_allowed3():
    e=MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    # user f is not in Ego. He should have access to DACO, and cloud.
    d.handle_access_allowed('f')

    assert e.log_create_user == [('f', 'Person F')]
    assert e.log_ensure_access == [('f',True)]
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 1

    create =f"Created account for user f with name Person F"
    grant = f"Ensured user 'f' has daco access (cloud=True)"
    report = d.report_issues()
    assert report == [create, grant]

def test_denied1():
    e = MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    # user 'b' is in Ego, and should still keep EGO and Cloud

    # We shouldn't change or log anything
    d.handle_access_denied('b')
    assert e.log_create_user == []
    assert e.log_ensure_access == []
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 0

    report = d.report_issues()
    assert report == []

def test_denied3():
    e = MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    # user 'e' is in Ego, and has DACO, but not cloud.
    d.handle_access_denied('e')
    assert e.log_create_user == []
    assert e.log_ensure_access == []
    assert e.log_revoke_access == []
    assert e.log_revoke_cloud == ['e']
    assert e.called_get_daco_users == 0

    # ensure we logged the revoked access
    expected = f"Revoked cloud access for user 'e'"
    report = d.report_issues()
    assert report == [expected]


def test_denied2():
    e = MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)
    # user 'g' is in Ego, but no longer has DACO or cloud.
    d.handle_access_denied('g')
    assert e.log_create_user == []
    assert e.log_ensure_access == []
    assert e.log_revoke_access == ['g']
    assert e.log_revoke_cloud == []
    assert e.called_get_daco_users == 0

    # ensure we logged the revoked access
    expected = f"Revoked all daco access for user 'g':(user not in daco list)"
    report = d.report_issues()
    assert report == [expected]

def test_update_ego():
    e = MockEgoSuccess(ego)
    d = DacoClient(daco, cloud, e)

    d.update_ego()
    assert set(e.log_create_user) == {('d','Person D'),('f','Person F')}
    assert set(e.log_ensure_access) == {('a',False),('b',True),('d',False),
                                        ('e',False), ('f', True)}
    assert set(e.log_revoke_access) == {'c', 'g', 'h'}
    assert set(e.log_revoke_cloud) == {'a','e'}
    assert e.called_get_daco_users == 6

    expected = {
        "Revoked all daco access for user 'c':(user in csa file but not in DACO file)",
        "Revoked all daco access for user 'g':(user in csa file but not in DACO file)",
        "Created account for user f with name Person F",
        "Ensured user 'f' has daco access (cloud=True)",
        "Ensured user 'b' has daco access (cloud=True)",
        "Ensured user 'a' has daco access (cloud=False)",
        "Created account for user d with name Person D",
        "Ensured user 'd' has daco access (cloud=False)",
        "Ensured user 'e' has daco access (cloud=False)",
        "Revoked cloud access for user 'a'",
        "Revoked all daco access for user 'h':(user not in daco list)",
        "Revoked cloud access for user 'e'"
    }

    report = d.report_issues()
    assert set(report) == expected
