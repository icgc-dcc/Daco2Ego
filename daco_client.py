def format_tuple(name, args):
    if len(args) == 1:
        return f"{name}({args[0]})"
    return f"{name}{args}"

def format_exception(e):
    return format_tuple(e.__class__.__name__, e.args)

def get_invalid_users(cloud, all_users):
    return [c for c in cloud if c not in all_users]

def get_valid_cloud_users(cloud_users, all_users):
    return {c for c in cloud_users if c in all_users}

class DacoClient(object):
    def __init__(self, users_map, cloud_map, ego_client, verbose=False):
        """
        :param users_map:
            An ordered dictionary of user_ids mapped to the CSV dictionary
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
        self.verbose_messages=verbose

        self.ego_client=ego_client
        self.daco_map = users_map

        all_users = list(users_map.keys())
        cloud_users = list(cloud_map.keys())

        self.invalid_users = get_invalid_users(cloud_users, all_users)
        self.all_users = all_users
        self.cloud_users = get_valid_cloud_users(cloud_users, all_users)

    def update_ego(self):
        """ Handle scenarios 1-4 wiki specification at
            https://wiki.oicr.on.ca/display/DCCSOFT/DACO2EGO

            Scenario 6 (error handling) is also handled implicitly by all
            calls to our ego client, which traps and logs all exceptions.

            returns: A list of issues encountered
        """
        # scenario 4 (revoke invalid )
        for user in self.invalid_users:
            self.handle_invalid_user(user)

        # scenarios 1 & 2 (grant access)
        for user in self.all_users:
            if user.find('@') == -1:
                self.log(f"Error: User '{user}' is not a valid email address")
                continue
            self.handle_access_allowed(user)

        # scenario 3 (revoke access)
        ego_users = self.get_ego_users()

        for user in ego_users:
            self.handle_access_denied(user)
        return self.report_issues()

    def get_user_name(self, user):
        name = None
        try:
            name = self.daco_map[user]
        except KeyError as e:
            self.err(f"Can't get name for user {user}", e)
        return name

    def has_cloud(self, user):
        return user in self.cloud_users

    # scenarios 1 & 2
    def handle_access_allowed(self, user):
        # scenario 1
        self.ensure_user_exists(user)

        # scenario 2
        self.ensure_access(user, self.has_cloud(user))

    # scenario 1 (create user if necessary)
    def ensure_user_exists(self, user):
        if not self.user_in_ego(user):
            name = self.get_user_name(user)
            # Scenario 1
            self.verbose(f"Creating ego user '{user}({name})")
            self.create_user(user,name)
        else:
            self.verbose(f"User {user} is already in ego")

    def user_in_ego(self, user):
        try:
            return self.ego_client.user_exists(user)
        except Exception as e:
            self.err(f"Can't tell if user '{user} exists in ego", e)

    # secenario 2 ( grant user correct permissions )
    def ensure_access(self, user, has_cloud):
        if not self.ego_has_daco(user):
            self.grant_daco(user)
        else:
            self.verbose(f"User '{user}' already has daco access")

        if has_cloud:
            if not self.ego_has_cloud(user):
                self.grant_cloud(user)
            else:
                self.verbose(f"User '{user} already has cloud access")

    # scenario 3 ( remove incorrect permissions )
    def handle_access_denied(self, user):
        if user not in self.daco_map:
            self.verbose(f"Ego user '{user}' is not on daco list")
            if self.ego_has_daco(user) or self.ego_has_cloud(user):
                self.revoke_access(user, "user not in daco list")
            else:
                self.err(f"Ego user '{user}' lost daco on their own???")
        elif user not in self.cloud_users:
            #self.verbose(f"Ego user '{user}' is not on cloud list")
            if self.ego_has_cloud(user):
                self.revoke_cloud(user)
            else:
                self.verbose(f"Ego user '{user}' doesn't have cloud access("
                             f"correct)")
        else:
            self.verbose(f"Ego user '{user}' has correct permissions")

    # Handle scenario 4 (User has cloud access, but not daco access)
    def handle_invalid_user(self, user):
       if self.ego_has_daco(user) or self.ego_has_cloud(user):
            self.revoke_access(user, "user in csa file but not in DACO file")
       else:
           self.verbose(f"Invalid user '{user} doesn't have DACO access")

    def get_ego_users(self):
        """ Get all users from ego with daco related policies
        """
        users = {}
        try:
            users = self.ego_client.get_daco_users()
        except Exception as e:
            self.err("Can't get list of daco users from ego", e)
        return users

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

    def grant_cloud(self, user):
        try:
            self.ego_client.grant_cloud(user)
            self.log(f"Granted cloud access to user '{user}'")
        except Exception as e:
            self.err(f"Can't grant cloud access to user '{user}'",e)

    def grant_daco(self, user):
        try:
            self.ego_client.grant_daco(user)
            self.log(f"Granted daco access to user '{user}'")
        except Exception as e:
            self.err(f"Can't grant daco access to user '{user}'", e)

    def ego_has_daco(self, user):
        try:
            return self.ego_client.has_daco(user)
        except Exception as e:
            self.err(f"Can't tell if user '{user}' has daco access", e)

    def ego_has_cloud(self, user):
        try:
            return self.ego_client.has_cloud(user)
        except Exception as e:
            self.err(f"Can't tell if user '{user}' has daco access", e)

    def report_issues(self):
        return self.issues_log

    def verbose(self, msg):
        if self.verbose_messages:
            self.log(msg)

    def log(self, msg):
        self.issues_log.append(msg)

    def err(self, msg, e):
        self.issues_log.append(f"Error: {msg} -- {format_exception(e)}")

