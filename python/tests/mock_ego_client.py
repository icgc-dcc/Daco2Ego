from collections import OrderedDict


def methods(cls):
    return {k for k in dir(cls) if not k.startswith('_')}


class MockIO(object):
    def __init__(self, *args, **kwargs):
        self.call_log = OrderedDict()

    def get_calls(self):
        return self.call_log

    def log_call(self, key, value):
        if key not in self.call_log:
            self.call_log[key] = []
        self.call_log[key].append(value)


class MockEgoSuccess(MockIO):
    def __init__(self, groups):
        super(MockEgoSuccess, self).__init__()
        self.groups = groups

    def get_users(self, group):
        self.log_call('get_users', group)
        return self.groups[group]

    def is_member(self, group, user):
        self.log_call('is_member',(group,user))
        return user in self.groups[group]

    def user_exists(self, user):
        print(f"Checking to see if user {user} exists")
        self.log_call('user_exists', user)
        for g in self.groups.values():
            if user in g:
                return True
        self.log_call('ego_user_not_found', user)
        return False

    def add(self, group, users):
        assert len(users) == 1
        self.log_call('add', (group,users[0]))
        self.groups[group] += users

    def remove(self, group, users):
        assert len(users) == 1
        self.log_call('remove',(group, users[0]))
        self.groups[group] += users


class MockEgoException(Exception):
    pass


def fmt_tuple(t):
    """
    Format a tuple as a set of items in parenthesis
    :param t: A tuple
    :return: A string containing the formatted tuple
    """
    if len(t) == 1:
        return f"({t[0]})"
    return f"{t}"


def ex_name(name, *args):
    """
    :param name: A method name
    :param args: A tuple of arguments to method, including the self object
    :return: The string that looks like the method call
    """
    return f"{name}{fmt_tuple(args)}"


def fail(f):
    def raise_mock(*args, **kwargs):
        f(*args, **kwargs)
        s = ex_name(f.__name__, *args[1:])
        raise MockEgoException(s)

    return raise_mock


class MockEgoFailure(MockEgoSuccess):
    pass


# For all of the methods from MockEgoSuccess, run that method, then
# throw an exception
for m in methods(MockEgoSuccess) - methods(MockIO):
    setattr(MockEgoFailure, m, fail(getattr(MockEgoSuccess, m)))
del globals()['m']
