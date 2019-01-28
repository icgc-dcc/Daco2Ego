class EgoClient(object):
    daco_names = {'portal'}
    cloud_policy_names = {'aws', 'collab'}
    all_names = daco_names | cloud_policy_names

    def __init__(self):
        self.rest_client = None
        self.policy_map= None
        self.user_cache = None
        self.mocks = {}

    def _get(self, endpoint):
        # append header 'Authorization:' <our authorization token>
        # return self.rest_client.get(headers, endpoint)
        print(f"Connecting to {endpoint}")
        return self.mocks[endpoint]

    def _post(self, endpoint, data):
        # append header 'Authorization:' <our authorization token>
        # return self.rest_client(headers, endpoint)
        return self.mocks[endpoint]

    def _delete(self, endpoint):
        return self.mocks[endpoint]

    def get_policies(self):
        return self._get("/policies")

    def get_users(self, policy_id):
        self._get(f"/policies/{policy_id}/users")

    def create_user(self, user, name):
        json = f'''
        \{ "email": {user},
           "name": {name},
        \}
        '''
        return self._post("/users", json)

    def get_user_permissions(self, user):
        # TODO Write me
        pass

    def delete_user_permission(self,user_id, permission_id):
        return self._delete(f"users/{user_id}/permissions/{permission_id}")

    def grant_user_permission(self, user, policy_id, mask):
        user_id = self._ego_user_id(user)
        json = f'''
        [ \{ "mask": "{mask}",
             "policy_id": "{policy_id}",
          \}
        ]
        '''
        return self._post(f"/users/{user_id}/permissions", json)


    def revoke_access(self, user):
        for policy_id in self._all_policy_ids():
            self._revoke_permission(user, policy_id)

    def revoke_cloud(self, user):
        for policy_id in self._cloud_policy_ids():
            self._revoke_permission(user, policy_id)

    def get_daco_users(self):
        if self.user_cache is None:
            self._set_user_cache()
        return self.user_cache.keys()

    def get_daco_policies(self, grant_cloud):
        if grant_cloud:
            return self._all_policy_ids()
        else:
            return self._daco_policy_ids()

    def _revoke_permission(self, user, policy_id):
        user_id = self._ego_user_id(user)
        self.delete_user_permission(user_id, policy_id)

    # We translate policy names (which define DACO) into ego ID numbers,
    # which ego uses internally, and cache them for efficiency.

    # Similarly, we need to use the EGO specific user-id rather than the
    # email field that daco uses to identify the user

    # We cache a map of the policy names to the DACO policies, and their
    # categories (only 3).

    # We also keep a mapping of all of the users with DACO related permissions
    # from their DACO id to their EGO id, so that we can update the ego
    # permissions for a given DACO user as necessary.
    def _ego_user_id(self, user):
        """ Get the ego user id for the given user from the cache
            Create cache by querying ego if we haven't done it yet.
        """
        if self.user_cache is None:
            self._set_user_cache()
        return self.user_cache[user]

    def _get_policy_map(self):
        """
        Query ego for all of the policies, and
        create map of policy names to policy ids
        """
        policy_map = {}
        data = self.get_policies()
        for row in data['result_set']:
            policy_map[row['name']] = row['id']
        return policy_map

    def _set_policies(self):
        """
            Convert our sets of policy names to set of policy_ids within ego.
        """
        policy_map = self._get_policy_map()
        def p(name):
            return policy_map[name]

        self.all_policies = set(map(p, self.all_names))
        self.daco_policies = set(map(p, self.daco_names))
        self.cloud_policies = set(map(p, self.cloud_policy_names))

    def _all_policy_ids(self):
        if self.all_policies is None:
            self._set_policies()
        return self.all_policies

    def _cloud_policy_ids(self):
        if self.cloud_policies is None:
            self._set_policies()
        return self.cloud_policies

    def _daco_policy_ids(self):
        if self.daco_policies is None:
            self._set_policies()
        return self.daco_policies

    def _update_users(self, user, user_id):
        if self.user_cache is None:
            self._set_user_cache()
        self.user_cache[user] = user_id

    def _set_user_cache(self):
        cache = {}
        for policy_id in self._all_policy_ids():
            users = self.get_users(policy_id)
            for u in users:
                cache[u['name']] = u['id']
        self.user_cache = cache

    def ensure_access(self, user, grant_cloud):
        permissions = self.get_user_permissions(user)['resultSet']
        policies = self.get_daco_policies(grant_cloud)

        for policy_id in policies:
            need_permission = self._has_policy(policy_id, permissions)
            if need_permission:
                    self.grant_user_permission(user, policy_id,"READ")

    def _has_policy(self, policy_id, permissions):
        for permission in permissions:
            if permission['policy']['id'] == policy_id:
                return True
        return False






