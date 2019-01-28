class DacoClient(object):
    def __init__(self, daco_map, cloud_map, ego_client):
        """
        :param daco_map:
            A dictionary of user_ids mapped to the dictionary of CSV keys
            (user name,openid,email,csa) read from our DACO file, indicating
            all the users who should have DACO access.

        :param cloud_map:
            A dictionary that of the same sort as above, but for users
            who should have cloud access.

        :param ego_client:
            An EgoClient object that applies the requested changes
            to the Ego server.
        """
        self.issues_log = []

        self.ego_client=ego_client
        self.daco_map = daco_map

        self.daco_users = daco_map.keys()
        self.cloud_users = cloud_map.keys()

    def update_ego(self):
        """ Handle scenarios 1-4 wiki specification at
            https://wiki.oicr.on.ca/display/DCCSOFT/DACO2EGO

            Scenario 6 (error handling) is also handled implicitly by all
            calls to our ego client, which traps and logs all exceptions.

            returns: A list of issues encountered
        """
        # scenario 4
        for user in self.invalid_users():
            self.handle_invalid_user(user)

        cloud_users = self.valid_cloud_users()
        daco_users = self.valid_daco_users()
        ego_users = self.get_ego_users()

        # scenarios 1 & 2
        for user in daco_users:
            self.handle_access_allowed(user)

        # scenario 3
        for user in ego_users:
            self.handle_access_denied(user)
        return self.report_issues()

    def invalid_users(self):
        return self.cloud_users - self.daco_users

    def valid_daco_users(self):
        return self.daco_users - self.invalid_users()

    def valid_cloud_users(self):
        return self.cloud_users - self.invalid_users()

    def get_user_name(self, user):
        name = None
        try:
            name = self.daco_map[user]
        except KeyError as e:
            self.err(f"Can't get name for user {user}", e)
        return name

    def grant_cloud(self, user):
        return user in self.valid_cloud_users()

    # scenarios 1 & 2
    def handle_access_allowed(self, user):
        if user not in self.get_ego_users():
            # Scenario 1
           self.create_user(user,self.get_user_name(user))
        # scenario 2
        self.ensure_access(user, self.grant_cloud(user))

    # scenario 3
    def handle_access_denied(self, user):
        if user not in self.valid_daco_users():
            self.revoke_access(user, "user not in daco list")
        elif user not in self.valid_cloud_users():
            self.revoke_cloud(user)

    # Handle scenario 4 (User has cloud access, but not daco access)
    def handle_invalid_user(self, user):
        self.revoke_access(user, "user in csa file but not in DACO file")

    def get_ego_users(self):
        """ Get all users from ego with daco related policies
        """
        users = []
        try:
            users = self.ego_client.get_daco_users()
        except Exception as e:
            self.err("Can't get list of daco users from ego:", e)
        return users

    def log(self, msg):
        self.issues_log.append(msg)

    def err(self, msg, e):
        self.issues_log.append(f"Error: {msg} -- {repr(e)}")

    # scenario 1
    def create_user(self, user, name):
        try:
            self.ego_client.create_user(user, name)
            self.log(f"Created account for user {user} with name {name}")
        except Exception as e:
            self.err(f"Can't create user '{user}'", e)

    def revoke_access(self, user, reason):
        try:
            self.ego_client.revoke_access(user)
            self.log(f"Revoked all daco access for user '{user}':({reason})")
        except Exception as e:
            self.err(f"Can't revoke daco access for user '{user}'", e)

    def revoke_cloud(self, user):
        try:
            self.ego_client.revoke_cloud(user)
            self.log(f"Revoked cloud access for user '{user}'")
        except Exception as e:
            self.err(f"Can't revoke cloud access for user '{user}'", e)

    def ensure_access(self, user, grant_cloud):
        try:
            self.ego_client.ensure_access(user, grant_cloud)
            self.log(f"Ensured user '{user}'"
                     f" has daco access "
                     f"(cloud={grant_cloud})")
        except Exception as e:
            self.err(f"Can't ensure access for user '{user}'"
                    f"(cloud={grant_cloud})", e)

    def report_issues(self):
        return self.issues_log
