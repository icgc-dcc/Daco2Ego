#!/usr/bin/python
class User(object):
    def __init__(self, email,name, has_daco, has_cloud):
        self.name = name
        self.email = email
        self.has_daco=has_daco
        self.has_cloud = has_cloud

    def invalid_email(self):
        """
        Is user's email clearly invalid?
        :param user: User's email
        :return: False if the email is invalid, True if it might be valid.
        """
        return self.email.find('@') == -1

    def is_invalid(self):
        """ User is invalid if they have cloud, but not daco access.
        """
        return self.has_cloud and not self.has_daco

    def __str__(self):
        return f"{self.email}({self.name})"