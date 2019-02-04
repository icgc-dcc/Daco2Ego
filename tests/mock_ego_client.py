from collections import OrderedDict
methods=lambda cls: {k for k in dir(cls) if not k.startswith('_')}

class MockIO(object):
    def __init__(self, *args, **kwargs):
        super(MockIO, self).__init__(*args, **kwargs)
        self.call_log=OrderedDict()

    def get_calls(self):
        return self.call_log

    def log_call(self, key, value):
        if key not in self.call_log:
            self.call_log[key]=[]
        self.call_log[key].append(value)

class MockEgoSuccess(MockIO):
    def __init__(self, users):
        super(MockEgoSuccess, self).__init__()
        self._daco_users = OrderedDict(users)

    def get_daco_users(self):
        self.log_call('get_daco_users', 'Called')
        return self._daco_users.keys()

    def user_exists(self, user):
        self.log_call('user_exists', user)
        return user in self._daco_users

    def create_user(self, user, name):
        self._daco_users[user] = (False, False)
        self.log_call('create_user', (user,name))

    def has_daco(self, user):
        self.log_call('has_daco', user)
        try:
            return self._daco_users[user][0]
        except KeyError:
            raise MockEgoException(f"User '{user}' does not exist in ego")

    def grant_daco(self, user):
        cloud=self._daco_users[user][1]
        self._daco_users[user]=(True, cloud)
        self.log_call('grant_daco', user)

    def revoke_access(self, user):
        self._daco_users[user]=(False, False)
        self.log_call('revoke_access', user)

    def has_cloud(self, user):
        self.log_call('has_cloud', user)
        try:
            return self._daco_users[user][1]
        except KeyError:
            raise MockEgoException(f"User '{user}' does not exist in ego")

    def grant_cloud(self, user):
        self._daco_users[user] = (True, True)
        self.log_call('grant_cloud', user)

    def revoke_cloud(self, user):
        self._daco_users[user]=(True, False)
        self.log_call('revoke_cloud', user)

def log_function(f):
    def wrapper(self, *args, **kwargs):
        f(self, *args, **kwargs)
        self.log_call(f.__name__, args)

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
        s=ex_name(f.__name__,*args[1:])
        raise MockEgoException(s)
    return raise_mock

class MockEgoFailure(MockEgoSuccess):
    pass

# For all of the methods from MockEgoSuccess, run that method, then
# throw an exception
for m in methods(MockEgoSuccess) - methods(MockIO):
    setattr(MockEgoFailure, m, fail(getattr(MockEgoSuccess, m)))
del globals()['m']