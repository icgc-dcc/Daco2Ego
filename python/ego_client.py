import json


class EgoClient(object):
    def __init__(self, base_url, rest_client):
        self.base_url = base_url

        self._rest_client = rest_client
        self._rest_client.stream = False

    def _get(self, endpoint):
        r = self._rest_client.get(self.base_url + endpoint)
        if r.ok:
            return r.text
        raise IOError(f"Error trying to GET {r.url}", r)

    def _get_json(self, endpoint):
        result = self._get(endpoint)
        j = json.loads(result)
        return j

    def _post(self, endpoint, data):
        headers = {'Content-type': 'application/json'}
        r = self._rest_client.post(self.base_url + endpoint, data=data,
                                   headers=headers)
        if r.ok:
            return r.text
        raise IOError(f"Error trying to POST to {endpoint}", r, data)

    def _delete(self, endpoint):
        return self._rest_client.delete(self.base_url + endpoint)

    def _field_search(self, endpoint, name, value):
        query = endpoint + f"?{name}={value}&limit=9999999"
        result = self._get_json(query)
        if result['count'] == 0:
            raise IOError(f"No matches for {value} from ego endpoint {query}",
                          result)

        # Return only exact matches from the field search
        matches = [item for item in result['resultSet']
                   if item[name].lower() == value.lower()]
        if not matches:
            raise LookupError(f"Can't find {value} in results from endpoint "
                              f"{query}", result)
        return matches

    # Public api
    def _group_id(self, group):
        """
        Return the group id for a group name
        :param group:
        :return:
        """
        group_ids = self._field_search("/groups", "name", group)
        if len(group_ids) > 1:
            raise LookupError(f"Multiple ids matched group '{group}': {group_ids}")
        return group_ids[0]['id']

    def _user_id(self, user):
        user_ids = self._field_search("/users", "email", user)
        if len(user_ids) > 1:
            raise LookupError(f"Multiple ids matched user '{user}': {user_ids}")
        return user_ids[0]['id']

    def get_users(self, group):
        """
        Return a list of users in the given group
        :param group:
        :return:
        """
        group_id = self._group_id(group)
        results = self._get_json(f"/groups/{group_id}/users?limit=9999999")

        return {user['email'] for user in results['resultSet']}

    def is_member(self, group, user):
        """
        Returns true if the user is a member of the group
        :param user:
        :param group:
        :return:
        """
        return user in self.get_users(group)

    def user_exists(self, user):
        """
        Returns true if the user exists in ego.
        :param user:
        :return:
        """
        try:
            self._user_id(user)
        except LookupError:
            return False
        return True

    def create_user(self, user, name, ego_type="USER"):
        first, _, last = name.rpartition(" ")
        j = json.dumps({"email": user, "firstName": first, "lastName": last, "type": ego_type,
                        "status": "APPROVED"})
        reply = self._post("/users", j)
        r = json.loads(reply)
        return r

    def add(self, group, users):
        """
        Add the users to the given group.
        :param group:
        :param users:

        :return:
        """
        user_ids = list(map(self._user_id, users))
        group_id = self._group_id(group)
        j = json.dumps(user_ids)
        return self._post(f"/groups/{group_id}/users", j)

    def remove(self, group, users):
        """
        Remove the users from the given group.
        :param group:
        :param users:
        :return:
        """
        user_ids = list(map(self._user_id, users))
        group_id = self._group_id(group)
        j = ",".join(user_ids)
        return self._delete(f"/groups/{group_id}/users/{j}")
