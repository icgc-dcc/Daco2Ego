#!/usr/bin/env python3
from tests.integration.fuzz import m, user_line, coin_flip, randint, random_user
from subprocess import run, PIPE


def main():
    users = []
    ego = {}
    config_file = "fuzz.conf.test"
    daco_filename = "fuzz.daco.csv"
    cloud_filename = "fuzz.cloud.csv"
    while randint(0, 10):
        new = permute(users)
        generate_files(daco_filename, cloud_filename, new)
        expected_report, expected_ego = expected_results(new, ego)
        actual_report = run_daco2_ego(config_file)
        compare_results(actual_report, expected_report)
        users = new
        ego = expected_ego


def run_daco2_ego(config_file):
    report = run(["../../daco2ego.py", config_file], encoding='UTF-8', stdout=PIPE)
    return report


def permute(users):
    for i, u in enumerate(users):
        if coin_flip():
            users[i] = modify_user(u)

    for i in range(randint(1, 5)):
        u = random_user()
        users.append(u)
    return users


def generate_files(daco_filename, cloud_filename, users):
    files = (daco_filename, cloud_filename)
    header = "user name,openid,email,csa\n"

    daco, cloud = m(lambda f: open(f, "w"), files)

    # create our baseline of users
    daco.write(header)
    cloud.write(header)

    for u in users:
        daco.write(user_line(u))
        if u.has_cloud:
            cloud.write(user_line(u))

    daco2, cloud2 = m(lambda f: open(f + "2", "w"), files)

    daco2.write(header)
    cloud2.write(header)

    daco2.close()
    cloud2.close()
    run(["./encrypt.sh", daco_filename])
    run(["./encrypt.sh", cloud_filename])


def modify_user(u):
    u.has_daco = coin_flip()
    u.has_cloud = coin_flip()

    return u


def add_perm(user):
    if user.has_daco and user.has_cloud:
        return "daco and cloud"
    elif user.has_daco:
        return "daco"
    else:
        return "Error"


def expected_results(new, ego):
    new_ego = {}
    results = []
    for u in new:
        results.append(classify(u, ego))
        new_ego[u.email] = (u.has_daco, u.has_cloud)
    return results, new_ego


def classify(u, ego):
    pass


def compare_results(expected, actual):
    pass


if __name__ == "__main__":
    main()
