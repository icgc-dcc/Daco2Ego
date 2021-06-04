from format_errors import err_msg
from daco_user import User


class DacoClient(object):
    def __init__(self, daco_group, cloud_group, users, ego_client):
        """
        :param users: A list of User objects

        :param ego_client:
            An EgoClient object that applies the requested changes
            to the Ego server.
        """
        self.ego_client = ego_client
        self.users = users
        self.daco_group = daco_group
        self.cloud_group = cloud_group
        # make a map of ego id == user.email to user, so that we can
        # find ego users with daco permissions.
        self._user_map = {u.email.lower(): u for u in users}
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
            self._counts[category][0] += 1
        except KeyError:
            self._counts[category] = [1, err]

    def get_summary(self):
        counts = {k: v[0] for k, v in self._counts.items() if not v[1]}
        errors = [f"*Error:* Ego operation *{k}* failed for {v[0]} users" for k, v in self._counts.items() if v[1]]
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
            return [err_msg("Can't get list of daco_users from ego", e)]
        return self.revoke_users(users)

    def get_daco_users_from_ego(self):
        return self.get_ego_users(self.fetch_ego_ids())

    def get_ego_users(self, ego_id_list):
        return map(self.get_user, ego_id_list)

    def get_user(self, ego_id):
        try:
            return self._user_map[ego_id.lower()]
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
            return f"Warning: User '{user}' is invalid " \
                f"(in cloud file, but not in DACO)"

        if self.ego_client.user_exists(user.email):
            return self.existing_user(user)

        self.count('ego_user_not_found')
        return f"User is not in ego, no access granted to '{user}'"


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
            self.revoke_cloud(user)
            self.count('revoke_invalid')
            return f"Revoked all access for invalid user '{user}':(on " \
                f"cloud access list, but not DACO)"

        if not user.has_daco and (self.has_daco(user) or self.has_cloud(user)):
            self.count('revoke_daco')
            self.revoke_daco(user)
            self.revoke_cloud(user)
            return f"Revoked all access for user '{user}'"

        if not user.has_cloud and self.has_cloud(user):
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
            daco_users = set(self.ego_client.get_users(self.daco_group))
            cloud_users = set(self.ego_client.get_users(self.cloud_group))
            return daco_users | cloud_users
        except Exception as e:
            raise LookupError(msg, e)

    def user_exists(self, user):
        try:
            return self.ego_client.user_exists(user.email)
        except Exception as e:
            self.count('user exists check', err=True)
            self.count(f"Ego user not found for user `{user}'", err=True)
            raise LookupError(f"Can't tell if user '{user} is already in "
                              f"ego", e)

    def ego_user_not_found(self, user, msg=None):
        if msg is None:
            msg = f"User does not exist in ego, no access changes for '{user}'"
        try:
            self.ego_client
        except Exception as e:
            self.count(f"Ego user not found for user `{user}'", err=True)
            raise LookupError(msg, e)

    def has_daco(self, user, msg=None):
        if msg is None:
            msg = f"Can't determine if user '{user}' has daco access"
        try:
            return self.ego_client.is_member(self.daco_group, user.email)
        except Exception as e:
            self.count("has DACO permission check", err=True)
            raise LookupError(msg, e)

    def has_cloud(self, user, msg=None):
        if msg is None:
            msg = f"Can't determine if user '{user}' has cloud access"
        try:
            return self.ego_client.is_member(self.cloud_group, user.email)
        except Exception as e:
            self.count("has cloud access check", err=True)
            raise LookupError(msg, e)

    def grant_daco(self, user, msg=None):
        if msg is None:
            msg = f"Can't grant daco access to user '{user}'"
        try:
            self.ego_client.add(self.daco_group, [user.email])
        except Exception as e:
            self.count("grant DACO access", err=True)
            raise LookupError(msg, e)

    def grant_cloud(self, user, msg=None):
        if msg is None:
            msg = f"Can't grant cloud access to user '{user}'"
        try:
            self.ego_client.add(self.cloud_group, [user.email])
        except Exception as e:
            self.count("grant cloud access", err=True)
            raise LookupError(msg, e)

    def revoke_daco(self, user, msg=None):
        if msg is None:
            msg = f"Can't revoke daco access for user '{user}'"
        try:
            self.ego_client.remove(self.daco_group, [user.email])
        except Exception as e:
            self.count("revoke DACO access", err=True)
            raise LookupError(msg, e)

    def revoke_cloud(self, user, msg=None):
        if msg is None:
            msg = f"Can't revoke cloud access for user '{user}'"
        try:
            self.ego_client.remove(self.cloud_group, [user.email])
        except Exception as e:
            self.count("revoke cloud access", err=True)
            raise LookupError(msg, e)
