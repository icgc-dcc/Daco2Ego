import json
class EgoClient(object):
    daco_policies = {'portal'}
    cloud_policies = {'aws', 'collab'}
    all_policies = daco_policies | cloud_policies

    def __init__(self, base_url, auth, rest_client):
        self.auth = auth
        self.base_url = base_url

        self._policy_map=None       # dict of { policy_name : policy_id }
        self._permission_map=None   # dict of { policy_name: set( user_name) }
        self._user_map=None         # dict of { user_name: user_id }
        self._ego_users=None        # set( user_name )
        self._rest_client = rest_client
        self._rest_client.stream = False

    def _get(self, endpoint):
        # append header 'Authorization:' <our authorization token>
        # return self.rest_client.get(headers, endpoint)
        #print(f"Connecting to {endpoint}")
        headers = {'Authorization': self.auth}
        r=self._rest_client.get(self.base_url + endpoint, headers=headers)
        if r.ok:
            return r.text
        raise IOError("Error trying to GET {r.url}",r)

    def _get_json(self, endpoint):
        result = self._get(endpoint)
        j = json.loads(result)
        return j

    def _post(self, endpoint, data):
        # append header 'Authorization:' <our authorization token>
        # return self.rest_client(headers, endpoint)
        #print(f"Posting to {endpoint}")
        headers = {'Authorization': self.auth, 'Content-type':
            'application/json'}
        r=self._rest_client.post(self.base_url + endpoint, data=data,
                                 headers=headers)
        if r.ok:
            return r.text
        raise IOError(f"Error trying to POST to {endpoint}",r, data)

    def _delete(self, endpoint):
        #print(f"Deleting from {endpoint}")
        headers = {'Authorization': self.auth}
        return self._rest_client.delete(self.base_url + endpoint, headers=headers)

    def _field_search(self, endpoint, name, value):
        query = endpoint + f"?{name}={value}&limit=9999999"
        result = self._get_json(query)
        if result['count'] == 0:
            raise IOError(f"No matches for {value} from ego endpoint {query}",
                          result)

        # Return only exact matches from the field search
        matches= [item for item in result['resultSet']
                              if item[name] == value ]
        if not matches:
            raise IOError(f"Can't find {value} in results from endpoint "
                          f"{query}", result)
        return matches

    def _get_policies(self):
        return self._get_json("/policies?limit=999999999")

    def _get_policy(self, policy_name):
        items = self._field_search("/policies", "name", policy_name)
        if len(items) > 1:
            raise IOError(f"Found multiple policies with name '{policy_name}'",
                          items)
        return items[0]

    def _get_policy_users(self, permission_name):
        """
        Get a list of all the users who have the given permission
        :param permission_name: An ego policy name (permission name)
        :return:
        """
        policy_id = self._get_policy_id(permission_name)
        users=self._get_json(f"/policies/{policy_id}/users")
        # This is actually the email, even though it says name
        return { u['name'].lower() for u in users}

    def _get_user_permissions(self, user):
        m = self._get_permission_map()
        return {p for p in self.all_policies if user in m[p]}

    def _get_permission_map(self):
        if not self._permission_map:
            self._permission_map=self._create_permission_map()
        return self._permission_map

    def _create_permission_map(self):
        m = {}
        for p in self.all_policies:
            m[p] = self._get_policy_users(p)
        return m

    def _delete_user_permission(self, user_id, permission_id):
        r = self._delete(f"/users/{user_id}/permissions/{permission_id}")
        if r.ok:
            return r
        raise IOError("Can't delete {permission_id} for user_id {user_id}",r)

    def _grant_user_permission(self, user_id, policy_id, mask):
        j = json.dumps([{ "mask": mask, "policyId": policy_id}])
        return self._post(f"/users/{user_id}/permissions", j)

    ### Public api
    def get_daco_users(self):
        m = self._get_permission_map()

        users = set()
        for permission in self.all_policies:
            users |= m[permission]
        return users

    def user_exists(self, user):
        if self._ego_users is None:
            self._ego_users = self._get_ego_users()
        return user in self._ego_users

    def _get_ego_users(self):
        r=self._get_json("/users?limit=9999999")
        return {u['email'].lower() for u in r['resultSet']}

    def create_user(self, user, name, ego_type="USER"):
        j = json.dumps({"email": user, "name":name, "userType": ego_type,
                       "status": "Approved" })
        reply=self._post("/users", j)
        r = json.loads(reply)
        self._set_id(r['name'],r['id'])
        if not self.user_exists(user):
            self._ego_users.add(user)
        return r

    def has_policies(self,user, policies):
        m = self._get_permission_map()
        if all(map(lambda p: user in m[p], policies)):
            return True
        return False

    def has_daco(self, user):
        return self.has_policies(user, self.daco_policies)

    def has_cloud(self, user):
        return self.has_policies(user, self.cloud_policies)

    def grant_daco(self, user):
        m = self._get_permission_map()
        for p in self.daco_policies:
            if user not in m[p]:
                self._grant_permissions(user, p)

    def grant_cloud(self, user):
        m = self._get_permission_map()
        for p in self.all_policies:
            if user not in m[p]:
                self._grant_permissions(user, p)

    def _grant_permissions(self, user, policy):
        #print(f"Granting permissions to {user} with names {policy}")

        policy_id = self._get_policy_id(policy)
        user_id = self._user_id(user)
        self._grant_user_permission(user_id, policy_id, 'READ')

    def revoke_daco(self, user):
        return self.revoke_policies(user, self.all_policies)

    def revoke_cloud(self, user):
        return self.revoke_policies(user, self.cloud_policies)

    def revoke_policies(self, user, policies):
        permissions = self._get_user_permissions(user)

        for policy_name in policies:
            for p in permissions:
                if p['policy']['name'] == policy_name:
                    permission_id = p['id']
                    self._revoke_permission(user, permission_id)

    def _revoke_permission(self, user, permission_id):
        user_id = self._user_id(user)
        self._delete_user_permission(user_id, permission_id)

    def _user_id_old(self, user):
        """
        Find the user's ego id based upon their email
        :param user: The user's email address (as stored in ego)
        :return: The user's ego id as a string (or an IOError is raised)
        """
        users = self._field_search("/users", "email", user)
        if len(users) > 1:
            raise IOError("Found multiple ids for user {user}", user)
        return users[0]['id']

    def _user_id(self, user):
        m = self._get_user_map()
        return m[user.lower()]

    def _set_id(self, user, id):
        m = self._get_user_map()
        m[user.lower()] = id

    def _get_user_map(self):
        if self._user_map is None:
            self._user_map = self._create_user_map()
        return self._user_map

    def _create_user_map(self):
        users = self._get_json("/users?limit=999999")
        return { u['name'].lower():u['id'] for u in users['resultSet'] }

    def _get_policy_id(self, name):
        m = self._get_policy_map()
        return m[name]

    def _get_policy_map(self):
        if self._policy_map is None:
            self._policy_map = self._create_policy_map()
        return self._policy_map

    # We translate policy names (which define DACO) into ego ID numbers,
    # which ego uses internally, and cache them for efficiency.
    def _create_policy_map(self):
        """
            Convert our sets of policy names to set of ego's policy_ids
        """
        policy_map = {}
        # get all the policy definitions from ego
        for name in self.all_policies:
            policy = self._get_policy(name)
            policy_map[name] = policy['id']
        return policy_map