class EgoClient(object):
    def __init__(self, base_url, mocks=None):
        if mocks is None:
            mocks = {}
        self.base_url = base_url
        self.mocks = mocks
        self.rest_client = None
        self.policy_map= None
        self.user_cache = None

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

    def add_scopes(self, user, scopes):

        for scope in scopes:
            return self._get(f"&user={user}&scopes={scopes}")

    def delete_user_permission(self,user_id, permission_id):
        return self._delete(f"users/{id}/permissions/{permission_id}")

    def grant_user_permission(self, user_id, policy_id, mask):
        json = f'''
        [ \{ "mask": "{mask}",
             "policy_id": "{policy_id}",
          \}
        ]
        '''
        return self._post(f"/users/{user_id}/permissions", json)

    def ensure_access(self, user, scopes):
        return self._get(f"add_access&user={user}&scopes={scopes}")