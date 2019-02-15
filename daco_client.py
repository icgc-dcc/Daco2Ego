from format_errors import err_msg
from user import User


class DacoClient(object):
    def __init__(self, users, ego_client):
        """
        :param users: A list of User objects

        :param ego_client:
            An EgoClient object that applies the requested changes
            to the Ego server.
        """
        self.ego_client = ego_client
        self.users = users
        # make a map of ego id == user.email to user, so that we can
        # find ego users with daco permissions.
        self._user_map = {u.email: u for u in users}
        self._counts = {}

    def update_ego(self):
        """ Handle scenarios 1-4 wiki specification at
            https://wiki.oicr.on.ca/display/DCCSOFT/DACO2EGO

            Scenario 6 (error handling) is also handled implicitly by all
            calls to our ego client, which traps and logs all exceptions.

            returns: A list of issues encountered
        """

        return (list(self.grant()) +
                list(self.revoke()))

    def count(self, category, err=False):
        try:
            self._counts[category][0]+=1
        except KeyError:
            self._counts[category] = [1, err]

    def get_summary(self):
        counts = {k:v[0] for k,v in self._counts.items() if not v[1]}
        errors = [ f"*Error:* Ego operation *{k}* failed for {v[0]} users" for k,v in self._counts.items() if v[1]]
        return counts, errors

    def grant(self):
        return self.grant_users(self.users)

    def grant_users(self, users):
        return filter(None, map(self.grant_user, users))

    def grant_user(self, user):
        try:
            return self.grant_access_if_necessary(user)
        except LookupError as e:
            return err_msg(e.args[0], e.args[1])

    def revoke(self):
        try:
            users = self.get_daco_users_from_ego()
        except Exception as e:
            return err_msg("Can't get list of daco_users from ego", e)
        return self.revoke_users(users)

    def get_daco_users_from_ego(self):
        return self.get_ego_users(self.ego_client.get_daco_users())

    def get_ego_users(self, ego_id_list):
        return map(self.get_user, ego_id_list)

    def get_user(self, ego_id):
        try:
            return self._user_map[ego_id]
        except KeyError:
            return User(ego_id, None, False, False)

    def revoke_users(self, users):
        return filter(None, map(self.revoke_user, users))

    def revoke_user(self, user):
        try:
            return self.revoke_access_if_necessary(user)
        except LookupError as e:
            return err_msg(e.args[0], e.args[1])

    def grant_access_if_necessary(self, user):
        if not self.is_unique_user(user):
            self.count("multiple_entries")
            return f"Warning: User '{user}' has multiple entries in the daco " \
                   f"file!"

        if user.invalid_email():
            self.count("invalid_email")
            return (f"Warning: User '{user}' does not have a valid email "
                    f"address")

        if user.is_invalid():
            self.count('invalid')
            return f"Warning: User '{user}' is invalid (in cloud file, but not in DACO)"

        if self.ego_client.user_exists(user.email):
            return self.existing_user(user)
        return self.new_user(user)

    # scenario 1
    def new_user(self, user):
        self.create_user(user)
        self.grant_daco(user)

        if not user.has_cloud:
            self.count('new_daco')
            return f"Created user '{user}' with daco access"

        self.grant_cloud(user)
        self.count('new_cloud')
        return f"Created user '{user}' with cloud access"

    # scenario 2
    def existing_user(self, user):
        granted_daco, granted_cloud = False, False

        if not self.has_daco(user):
            self.grant_daco(user)
            granted_daco = True

        if user.has_cloud and not self.has_cloud(user):
            self.grant_cloud(user)
            granted_cloud = True

        if granted_daco and granted_cloud:
            self.count('grant_both')
            return f"Granted daco and cloud to existing user '{user}'"
        elif granted_daco:
            self.count('grant_daco')
            return f"Granted daco to existing user '{user}'"
        elif granted_cloud:
            self.count('grant_cloud')
            return f"Granted cloud to existing user '{user}"
        else:
            # return f"Existing user '{user}' was set up correctly."
            return None

    def is_unique_user(self, user):
        u1 = self.get_user(user.email)
        return u1 == user

    # scenarios 3 and 4
    def revoke_access_if_necessary(self, user):
        if user.is_invalid():
            self.revoke_daco(user)
            self.count('revoke_invalid')
            return f"Revoked all access for invalid user '{user}':(on " \
                   f"cloud access list, but not DACO)"

        if not user.has_daco and self.has_daco(user):
            self.revoke_daco(user)
            self.count('revoke_daco')
            return f"Revoked all access for user '{user}'"

        if not user.has_cloud:
            if self.has_cloud(user):
                self.count('revoke_cloud')
                self.revoke_cloud(user)
                return f"Revoked cloud access for user '{user}'"
        return None

    #####################################################################
    # Wrap all exceptions from our ego_client as LookupErrors
    # with nice context based messages for us to display if they happen.
    ####################################################################
    def fetch_ego_ids(self, msg=None):
        """ Get all users from ego with daco related policies
        """
        if msg is None:
            msg = "Can't get list of daco users from ego"
        try:
            return self.ego_client.get_daco_users()
        except Exception as e:
            raise LookupError(msg, e)

    def user_exists(self, user):
        try:
            return self.ego_client.user_exists(user.email)
        except Exception as e:
            self.count('user exists check', err=True)
            raise LookupError(f"Can't tell if user '{user} is already in "
                              f"ego", e)

    def create_user(self, user, msg=None):
        if msg is None:
            msg = f"Can't create user '{user}'"
        try:
            self.ego_client.create_user(user.email, user.name)
        except Exception as e:
            self.count('create user', err=True)
            raise LookupError(msg, e)

    def has_daco(self, user, msg=None):
        if msg is None:
            msg = f"Can't determine if user '{user}' has daco access"
        try:
            return self.ego_client.has_daco(user.email)
        except Exception as e:
            self.count("has DACO permission check", err=True)
            raise LookupError(msg, e)

    def has_cloud(self, user, msg=None):
        if msg is None:
            msg = f"Can't determine if user '{user}' has cloud access"
        try:
            return self.ego_client.has_cloud(user.email)
        except Exception as e:
            self.count("has cloud access check", err=True)
            raise LookupError(msg, e)

    def grant_daco(self, user, msg=None):
        if msg is None:
            msg = f"Can't grant daco access to user '{user}'"
        try:
            self.ego_client.grant_daco(user.email)
        except Exception as e:
            self.count("grant DACO access", err=True)
            raise LookupError(msg, e)

    def grant_cloud(self, user, msg=None):
        if msg is None:
            msg = f"Can't grant cloud access to user '{user}'"
        try:
            self.ego_client.grant_cloud(user.email)
        except Exception as e:
            self.count("grant cloud access", err=True)
            raise LookupError(msg, e)

    def revoke_daco(self, user, msg=None):
        if msg is None:
            msg = f"Can't revoke daco access for user '{user}'"
        try:
            self.ego_client.revoke_daco(user.email)
        except Exception as e:
            self.count("revoke DACO access", err=True)
            raise LookupError(msg, e)

    def revoke_cloud(self, user, msg=None):
        if msg is None:
            msg = f"Can't revoke cloud access for user '{user}'"
        try:
            self.ego_client.revoke_cloud(user.email)
        except Exception as e:
            self.count("revoke cloud access", err=True)
            raise LookupError(msg, e)
