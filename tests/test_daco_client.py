#!/usr/bin/env python
from collections import OrderedDict

from daco_client import DacoClient
from user import User
from mock_ego_client import MockEgoFailure, MockEgoSuccess

user_list = [('a@ca', 'Person A', True, False),
             ('aa@ca', 'Person A', True, True),  # same name as A (ignored)
             ('b@ca', 'Person B', True, True),  # duplicate B (report error)
             ('b@ca', 'Person Bee', True, True),  # duplicate B (processed)
             ('c@ca', 'Person C', False, True),  # cloud only (invalid)
             ('d@ca', 'Person D', True, False),
             ('e@ca', 'Person E', True, True),
             ('f@ca', 'Person F', True, False),
             ('g@ca', 'Person G', True, True),
             ('h@ca', 'Person H', True, False),
             ('http://k.ca/openid/letmein', 'Person K', True, True)
             ]

users = list(map(lambda x: User(*x), user_list))

ego = OrderedDict({'a@ca': (False, False),  # grant daco
                   'aa@ca': (False, False),  # grant both (ignore name match)
                   'b@ca': (True, False),  # grant cloud
                   'c@ca': (False, True),  # revoke all (invalid)
                   # d@ca: create user, grant daco
                   # e@ca: create both
                   'f@ca': (True, False),  # do nothing
                   'g@ca': (True, True),  # do nothing
                   'h@ca': (True, True),  # revoke cloud
                   'i@ca': (True, False),  # revoke all
                   'j@ca': (True, True),  # revoke all
                   })


def daco_client(success=True):
    if success:
        e = MockEgoSuccess(ego)
    else:
        e = MockEgoFailure(ego)
    d = DacoClient(users, e)
    return d, e


def run_io_test_ok(method_name, args, compare):
    d, e = daco_client()
    m = getattr(d, method_name)
    result = m(*args)
    compare(result, e)


def run_io_test_fail(method_name, args, err_msg):
    d, e = daco_client(False)
    m = getattr(d, method_name)
    try:
        m(*args)
    except LookupError as ex:
        msg, err = ex.args
        assert msg == err_msg


def run_test(method_name, args, compare, err_msg):
    run_io_test_ok(method_name, args, compare)
    run_io_test_fail(method_name, args, err_msg)


def run_user_test(user, method_name, call_results, exception_message):
    def compare(result, e):
        assert result is None
        assert e.get_calls() == {method_name: call_results}

    run_test(method_name, (user,), compare, exception_message)


def run_io_tests():
    u = users[0]
    tests = {'create_user': ([(u.email, u.name)], f"Can't create user '{u}'"),
             'revoke_daco': ([u.email],
                             f"Can't revoke daco access for user '{u}'"),
             'revoke_cloud': ([u.email],
                              f"Can't revoke cloud access for user '{u}'"),
             'grant_daco': ([u.email],
                            f"Can't grant daco access to user '{u}'"),
             'grant_cloud': ([u.email],
                             f"Can't grant cloud access to user '{u}'"),
             }
    for k, v in tests.items():
        run_user_test(u, k, v[0], v[1])

        # map(lambda i:(lambda k,v:run_user_test(u,k,v[0],v[1]))(*i),
        #     tests.items())


def run_access_test(user, method, expected):
    def compare(result, e):
        if result != expected:
            print(f"user={user},method={method},expected={expected},"
                  f"result={result}")
        assert result == expected
        assert e.get_calls() == {f'has_{method}': [f'{user.email}']}

    msg = f"Can't determine if user '{user}' has {method} access"
    run_test(f'has_{method}', (user,), compare, msg)


def run_user_access_tests(user, has_daco, has_cloud):
    run_access_test(user, 'daco', has_daco)
    run_access_test(user, 'cloud', has_cloud)


def run_access_checks():
    data = [(users[0], False, False),  # exists, but no access
            (users[3], True, False),  # cloud only
            (users[5], False, False),  # doesn't exist
            (users[8], True, True),  # both daco and cloud
            ]
    map(lambda args: run_user_test(*args), data)


def check_exists(user, expected):
    def compare(result, e):
        assert result == expected
        assert e.get_calls() == {f'user_exists': [f'{user.email}']}

    run_test('user_exists', (user,), compare,
             f"Can't tell if user '{user} is already in ego")


def run_existence_checks():
    check_exists(users[0], True)  # a@ca is in ego
    check_exists(users[5], False)  # d@ca isn't


def run_get_users_test():
    def compare(result, e):
        assert e.get_calls() == {'get_daco_users': ['Called']}
        assert result == ego.keys()

    msg = f"Can't get list of daco users from ego"
    run_test('fetch_ego_ids', (), compare, msg)


def test_io():
    """
    Verify that our all ego_client wrapper calls call the expected
    ego method, (and no others!), and that they always
    throw a LookupError exception with the right message whenever
    the underlying ego_client throws any exception.
    :return:
    """
    run_io_tests()
    run_access_checks()
    run_existence_checks()
    run_get_users_test()


def test_get_user():
    e = None  # no ego client methods should be called! Fail if they are!
    d = DacoClient(users, e)
    user = users[0]  # Person A
    u = d.get_user(user.email)
    assert u == user


def test_is_unique():
    d = DacoClient(users, None)
    user1 = users[0]
    user2 = User(*user_list[0])

    assert user1 == user2

    assert d.is_unique_user(users[0])
    assert d.is_unique_user(users[1])
    assert not d.is_unique_user(users[2])  # duplicate, not last => False
    assert d.is_unique_user(users[3])  # last duplicate => True


def run_new_user_test(user, expected, calls):
    d, e = daco_client()
    result = d.new_user(user)
    assert result == expected
    assert e.get_calls() == calls


def test_new_user():
    def daco(u):
        return (f"Created user '{u}' with daco access",
                {'create_user': ([(u.email, u.name)]),
                 'grant_daco': ([u.email])
                 })

    def cloud(u):
        return (f"Created user '{u}' with cloud access",
                {'create_user': ([(u.email, u.name)]),
                 'grant_daco': ([u.email]),
                 'grant_cloud': ([u.email]),
                 }
                )

    data = [(users[5], daco),
            (users[6], cloud)]

    for user, access in data:
        msg, calls = access(user)
        run_new_user_test(user, msg, calls)


def run_existing_user_test(user, msg, calls):
    d, e = daco_client()
    result = d.existing_user(user)
    assert result == msg
    assert e.get_calls() == calls


def test_existing_user():
    data = [(users[0], True, False),
            (users[1], True, True),
            (users[3], False, True),
            (users[7], False, False)
            ]

    for user, grant_daco, grant_cloud in data:
        msg, calls = expected_grants(user, grant_daco, grant_cloud)
        run_existing_user_test(user, msg, calls)


def expected_grants(user, grant_daco, grant_cloud):
    e = [f'{user.email}']
    if grant_daco and grant_cloud:
        return (f"Granted daco and cloud to existing user '{user}'",
                {'has_daco': e,
                 'grant_daco': e,
                 'has_cloud': e,
                 'grant_cloud': e})
    elif grant_daco:
        return (f"Granted daco to existing user '{user}'",
                {'has_daco': e,
                 'grant_daco': e})
    elif grant_cloud:
        return (f"Granted cloud to existing user '{user}",
                {'has_daco': e, 'has_cloud': e, 'grant_cloud': e})
    else:
        # return f"Existing user '{user}' was set up correctly."
        return None, {'has_daco': e}


def run_test_revoke(user, expected, calls):
    d, e = daco_client()
    result = d.revoke_access_if_necessary(user)
    assert result == expected
    assert e.get_calls() == calls


def test_revoke_access_if_necessary():
    def invalid(u):
        return f"Revoked all access for invalid user " \
            f"'{u}':(on cloud access list, but not DACO)"

    def daco(u):
        return f"Revoked all access for user '{u}'"

    def cloud(u):
        return f"Revoked cloud access for user '{u}'"

    def ok(_u):
        return None

    data = [(users[4], invalid, {'revoke_daco'}),
            (users[8], ok, {}),
            (users[9], cloud, {'has_cloud', 'revoke_cloud'}),
            (User('i@ca', None, False, False), daco, {'has_daco', 'revoke_daco'}),
            (User('j@ca', None, False, False), daco, {'has_daco', 'revoke_daco'}),
            ]
    for user, f, call_names in data:
        e = [f'{user.email}']
        calls = {call: e for call in call_names}
        run_test_revoke(user, f(user), calls)


def run_test_grant(user, expected, calls):
    d, e = daco_client()

    # We've already tested new_user and existing_user, so just mock them
    # and note that we've called them so our tests can verify that we
    # got their results when we expected to.
    def new(u):
        e.log_call('new_user', u.email)
        return "new"

    def old(u):
        e.log_call('existing_user', u.email)
        return "old"

    d.new_user = new
    d.existing_user = old

    result = d.grant_access_if_necessary(user)
    assert result == expected
    c = e.get_calls()
    print(c)
    assert c == calls


def test_grant_access_if_necessary():
    def duplicate(u):
        return f"Warning: User '{u}' has multiple entries in the " \
            f"daco file!"

    def invalid_email(u):
        return f"Warning: User '{u}' does not have a valid " \
            f"email address"

    def invalid_user(u):
        return f"Warning: User '{u}' is invalid (in cloud file, but not in DACO)"

    def new_user(_u):
        return "new"

    def old_user(_u):
        return "old"

    data = [
        (users[0], old_user, {'user_exists', 'existing_user'}),
        (users[4], invalid_user, {}),
        (users[5], new_user, {'user_exists', 'new_user'}),
        (users[2], duplicate, {}),
        (users[10], invalid_email, {})
    ]

    for user, f, call_names in data:
        e = [f'{user.email}']
        calls = {call: e for call in call_names}
        run_test_grant(user, f(user), calls)


def test_update_ego():
    d, e = daco_client()

    report = d.update_ego()
    print(report)

    expected = ["Granted daco to existing user 'a@ca(Person A)'",
                "Granted daco and cloud to existing user 'aa@ca(Person A)'",
                "Warning: User 'b@ca(Person B)' has multiple entries in the "
                "daco file!",
                "Granted cloud to existing user 'b@ca(Person Bee)",
                "Warning: User 'c@ca(Person C)' is invalid (in cloud file, but not in DACO)",
                "Created user 'd@ca(Person D)' with daco access",
                "Created user 'e@ca(Person E)' with cloud access",
                "Warning: User 'http://k.ca/openid/letmein(Person K)' does not "
                "have a "
                "valid email address",
                "Revoked all access for invalid user 'c@ca(Person C)':(on "
                "cloud access "
                "list, but not DACO)",
                "Revoked cloud access for user 'h@ca(Person H)'",
                "Revoked all access for user 'i@ca(None)'",
                "Revoked all access for user 'j@ca(None)'"]

    assert report == expected

    print(e.get_calls())

    assert e.get_calls() == OrderedDict([
        ('user_exists', ['a@ca', 'aa@ca', 'b@ca', 'd@ca', 'e@ca',
                         'f@ca', 'g@ca', 'h@ca']),
        ('has_daco', ['a@ca', 'aa@ca', 'b@ca', 'f@ca', 'g@ca', 'h@ca', 'i@ca', 'j@ca']),
        ('grant_daco', ['a@ca', 'aa@ca', 'd@ca', 'e@ca']),
        ('has_cloud', ['aa@ca', 'b@ca', 'g@ca', 'a@ca', 'f@ca', 'h@ca',
                       'd@ca']),
        ('grant_cloud', ['aa@ca', 'b@ca', 'e@ca']),
        ('create_user', [('d@ca', 'Person D'), ('e@ca', 'Person E')]),
        ('get_daco_users', ['Called']),
        ('revoke_daco', ['c@ca', 'i@ca', 'j@ca']),
        ('revoke_cloud', ['h@ca'])])
