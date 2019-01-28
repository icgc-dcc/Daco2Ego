from ego_client import EgoClient

class DacoClient(object):
    def __init__(self, config, daco, cloud, client=None):
        """

        :param config:
        :param daco: A dictionary of user_ids mapped to the dictionary of CSV keys
                    read from our file. Each users in the dictionary should have
                    daco access. (user name,openid,email,csa)

        :param cloud:  A dictionary that of the same sort as above, for users
                    who should have cloud access.
        :param client:
        """
        if client is None:
            self.ego_client = EgoClient()
        else:
            self.ego_client = client

        self.issues_log = []
        self.ids = None

        self.daco_map = daco
        self.daco_users = daco.keys()
        self.cloud_users = cloud.keys()

    def update_ego(self):
        """ Handle scenarios 1-4 wiki specification at
            https://wiki.oicr.on.ca/display/DCCSOFT/DACO2EGO

            Scenario 6 (error handling) is also handled implictly by all
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
            self.handle_access_allowed(user, cloud_users, ego_users)

        # scenario 3
        for user in ego_users:
            self.handle_access_denied(user, daco_users, cloud_users)
        return self.report_issues()

    def invalid_users(self):
        return self.cloud_users - self.daco_users

    def valid_daco_users(self):
        return self.daco_users - self.invalid_users()

    def valid_cloud_users(self):
        return self.cloud_users - self.invalid_users()

    # scenarios 1 & 2
    def handle_access_allowed(self, user, cloud_users, ego_users):
        grant_cloud = user in cloud_users
        if user not in ego_users:
            # Scenario 1
           self.create_user(user,self.daco_map[user])
        # scenario 2
        self.ensure_access(user, grant_cloud)

    # scenarios 1
    def create_user(self, user, details):
        self.log(f"Creating account for user {user} with details {details}")
        try:
            self.ego_client.create_user(user, details['name'])
        except Exception as e:
            self.err("Can't create user {user}", e)

    # scenario 3
    def handle_access_denied(self, user, daco_users, cloud_users):
        if user not in daco_users:
            self.revoke_access(user, "user not in daco list")
        elif user not in cloud_users:
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
        self.issues_log.append("Error:" + msg + ":" + str(e))

    def revoke_access(self, user, reason):
        self.log(f"Revoking all daco access for user {user}: ({reason})")
        self.ego_client.revoke_access(user)

    def revoke_cloud(self, user):
        self.log(f"Revoking cloud access for user {user}")
        self.ego_client.revoke_cloud(user)

    def ensure_access(self, user, grant_cloud):
        self.log(f"Ensuring {user} has daco access(cloud={grant_cloud}")
        self.ego_client.ensure_access(user, grant_cloud)

    def report_issues(self):
        return self.issues_log
