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

    def __eq__(self, other):
        return (self.name == other.name and
               self.email == other.email and
               self.has_daco == other.has_daco and
               self.has_cloud == other.has_cloud)

    def __str__(self):
        return f"{self.email}({self.name})"

    def __repr__(self):
        return self.__class__.__name__ + f"({self.email},{self.name}," \
                                     f"{self.has_daco}, {self.has_cloud})"