class MockEgoSuccess(object):
    def __init__(self, users):
        self.log_create_user=[]
        self.log_ensure_access=[]
        self.log_revoke_access=[]
        self.log_revoke_cloud=[]
        self.called_get_daco_users = 0
        self.daco_users=users

    def create_user(self, user, details):
        self.log_create_user.append((user,details))

    def ensure_access(self, user, grant_cloud):
        self.log_ensure_access.append((user,grant_cloud))

    def revoke_access(self, user):
        self.log_revoke_access.append(user)

    def revoke_cloud(self, user):
        self.log_revoke_cloud.append(user)

    def get_daco_users(self):
        self.called_get_daco_users +=1
        return self.daco_users

class MockEgoException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"Ego exception:{self.msg} + failed"

class MockEgoFailure(MockEgoSuccess):
    def __init___(self):
        pass

    def create_user(self, user, details):
        super(MockEgoFailure, self).create_user(user, details)
        raise MockEgoException(f"create_user(user={user}, name={details})")

    def ensure_access(self, user, grant_cloud):
        super(MockEgoFailure, self).ensure_access(user, grant_cloud)
        raise MockEgoException(f"ensure_access(user={user}, "
                               f"grant={grant_cloud})")

    def revoke_access(self, user):
        super(MockEgoFailure, self).revoke_access(user)
        raise MockEgoException(f"revoke_access(user={user})")

    def revoke_cloud(self, user):
        super(MockEgoFailure, self).revoke_cloud(user)
        raise MockEgoException(f"revoke_cloud(user={user})")

    def get_daco_users(self):
        super(MockEgoFailure, self).get_daco_users()
        raise MockEgoException(f"get_daco_users()")