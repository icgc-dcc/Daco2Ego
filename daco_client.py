from ego_client import EgoClient

class DacoClient(object):
    daco_names = { 'portal' }
    cloud_policy_names = {'aws', 'collab'}
    all_names = daco_names | cloud_policy_names

    def __init__(self, config, client=None):
        if client == None:
            self.client = EgoClient(config['base_url'])
        else:
            self.client = client
        self.issues_log = []
        self.ids = None


    def log(self, msg):
        self.issues_log.append(msg)

    def err(self, msg, e):
        self.issues_log.append("Error:" + msg + ":" + str(e))

    def _id(self, user):
        """ Get the ego user id for the given user from the cache
            Create cache by querying ego if we haven't done it yet.
        """
        if self.user_cache is None:
            self._get_users()
        return self.user_cache[user]

    def _get_policy_users(self, policy_id):
        """ Return user permissions for the policy
            user_id, user_name, & mask.
        """
        try:
            data = self.client.get_users(policy_id)
            users = data['result_set']
        except Exception as e:
            msg = f""
            self.err(f"Can't get users for policy id {policy_id}", e)
            users=[]
        return users

    def _get_policy_map(self):
        """
        Connect to ego and create a cache of policy ids.
        We'll need them for our queries later on.
        """

        policy_map={}
        data = self.client.get_policies()
        for row in data['result_set']:
            policy_map[row['name']] = row['id']

        def p(name):
            return policy_map[name]
        self.all_policies = set(map(p, self.all_names))
        self.daco_policies = set(map(p, self.daco_names))
        self.cloud_policies = set(map(p, self.cloud_policy_names))
        return policy_map

    def _all_policy_ids(self):
        if self.all_policies is None:
            self._get_policy_map()
        return self.all_policies

    def _cloud_policy_ids(self):
        if self.cloud_policies is None:
            self._get_policy_map()
        return self.cloud_policies

    def _daco_policy_ids(self):
        if self.daco_policies is None:
            self._get_policy_map()
        return self.daco_policies

    def _get_users(self):
        """ Return all users with aws, portal, or collab
            policies.
        """
        if self.user_cache is not None:
            return self.user_cache
        users = {}
        for policy_id in self._all_policy_ids():
            policy_users = self._get_policy_users(policy_id)
            for u in policy_users:
                users[u['name']] = u['id']
        self.user_cache = users
        return users.keys()

    def _update_users(self, user, id):
        if self.user_cache is None:
            self._get_users()
        self.user_cache[user] = id

    def get_daco_users(self):
        try:
           users = self._get_users()
        except Exception as e:
            self.err("Can't get list of daco users from ego:", e)
            users= []
        return users

    def _revoke_permission(self, user, policy_id):
        user_id = self._id(user)
        try:
            self.client.remove_user_permissions(user_id, policy_id)
        except Exception as e:
            self.err(f"Couldn't revoke policy {policy_id} for user {user}"
                     f"({user_id})"
                     f"", e)

    def revoke_all(self, user, reason):
        self.log(f"Revoking all daco access for user {user}: ({reason})")
        for policy_id in self._all_policy_ids():
            self._revoke_permission(user, policy_id)

    def revoke_cloud(self, user):
        self.log(f"Revoking cloud access for user {user}")
        for policy_id in self._cloud_policy_ids():
            self._revoke_permission(user, policy_id)

    def create_user(self, user, details):
        self.log(f"Creating account for user {user} with details {details}")
        try:
            data = self.client.create_user(user,details['name'])
            self._update_users(user, data['id'])
        except Exception as e:
            self.err("Can't create user {user}",e)

    def _has_policy(self, policy_id, permissions):
        for permission in permissions:
            if permission['policy']['id'] == policy_id:
                return True
        return False

    def ensure_access(self, user, grant_cloud):
        self.log(f"Ensuring {user} has daco access(cloud={grant_cloud}")
        user_id = self._id(user)
        try:
            permissions = self.client.get_user_permissions(user_id)['resultSet']
        except Exception as e:
            self.err(f"Couldn't get user permissions for user {user}", e)
            permissions = []

        if grant_cloud:
            policies = self._all_policy_ids()
        else:
            policies = self._daco_policy_ids()

        for policy_id in policies:
            add_permission = self._has_policy(policy_id, permissions)
            if add_permission:
               self.log(f"Granting permission {policy_id} to user {user}")
               try:
                    self.client.grant_user_permission(user_id, policy_id,
                                                      "READ")
               except Exception as e:
                    self.err(f"Can't grant permission {policy_id} to user "
                             f"{user}",e)
            else:
                self.log(f"User {user} already has permission {policy_id}")

    def report_issues(self):
        return self.issues_log
