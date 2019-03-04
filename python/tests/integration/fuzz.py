#!/usr/bin/env python3
import sys
from daco_user import User
from random import randint


def m(f, c):
    return list(map(f, c))


def char_range(start, end):
    return list(map(chr, range(ord(start), ord(end))))


AtoZ = char_range('a', 'z') + char_range('A', 'Z')


def random_userlist(n):
    users = []
    for i in range(n):
        users.append(random_user())
    return users

def sequential_userlist(n):
    users = []
    for i in range(n):
        x = AtoZ[i]
        users.append(User(f"{x}@google.ca",f"User {x}",True, False))
    return users

def coin_flip():
    if randint(0, 1) == 1:
        return True
    return False


def random_character():
    # one in a thousand times, return a potentially invalid character
    if randint(1, 1000) == 1:
        return chr(randint(0, 255))

    return AtoZ[randint(0, len(AtoZ) - 1)]


def random_name():
    name = ""
    n = randint(1, 100)
    for _ in range(n):
        name += random_character()
    return name


def random_email():
    return random_name() + "@" + random_name()


def random_user():
    email = random_email()
    name = random_name()
    has_cloud = coin_flip()
    return User(email, name, True, has_cloud)


def user_line(u):
    return f"{u.name},{u.email},,{u.has_cloud}\n"


def main(_program_name, daco_filename, cloud_filename):
    files = (daco_filename, cloud_filename)
    header = "user name,openid,email,csa\n"

    daco, cloud = m(lambda f: open(f, "w"), files)

    # create our baseline of users
    daco.write(header)
    cloud.write(header)
    #users = random_userlist(5)
    users = sequential_userlist(5)
    for u in users:
        daco.write(user_line(u))
        if u.has_cloud:
            cloud.write(user_line(u))

    daco2, cloud2 = m(lambda f: open(f + "2", "w"), files)
    daco2.write(header)
    cloud2.write(header)

    for u in users:
        if coin_flip():
            cloud2.write(user_line(u))
        else:
            print(f"revoke cloud {u}")

        if u.has_cloud:
            if coin_flip():
                daco2.write(user_line(u))
            else:
                print(f"revoked daco {u}")
        else:
            if coin_flip():
                daco2.write(user_line(u))
                cloud2.write(user_line(u))
                print(f"Granted cloud for existing user {u}")

    for u in random_userlist(5):
        daco2.write(user_line(u))
        if u.has_cloud:
            cloud2.write(user_line(u))
            print(f"New cloud user {u}")
        else:
            print(f"New daco user {u}")


if __name__ == "__main__":
    main(*sys.argv)
