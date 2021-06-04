def zero_defaults(fields, dictionary):
    counts = {k: 0 for k in fields}
    counts.update(dictionary)
    return counts


def summarize(c):
    fields = ("new_daco", "new_cloud", "grant_daco", "grant_cloud", "grant_both",
              "revoke_daco", "revoke_cloud", "revoke_invalid", "ego_user_not_found")
    counts = zero_defaults(fields, c)

    counts['new'] = counts['new_daco'] + counts['new_cloud']
    counts['grant'] = counts['grant_cloud'] + counts['grant_both']  # grants to cloud
    counts['revoke'] = counts['revoke_daco'] + counts['revoke_invalid']  # revokes of cloud

    updates = (('new', "Added {new} users({new_daco} with DACO access, {new_cloud} with DACO & Cloud)."),
               ('grant_daco', "Granted DACO access to {grant_daco} existing users."),
               ('grant',
                "Granted DACO and Cloud access to {grant} existing users "
                "({grant_cloud} of them already had DACO)."),
               ('revoke_cloud', "Revoked Cloud access from {revoke_cloud} existing users."),
               ('revoke',
                "Revoked DACO and Cloud access from {revoke} existing users "
                "({revoke_invalid} of them were invalid users)."),
               ('ego_user_not_found', "{ego_user_not_found} users were not registered in Ego.")
               )

    report_fields = [u[0] for u in updates]
    if not any([counts[f] for f in report_fields]):
        return "*Updates*: No updates\n"

    report = "*Updates*:\n"
    for category, message in updates:
        try:
            if counts[category]:
                report += "\t" + message.format(**counts) + "\n"
        except KeyError:
            pass

    return report


def report_warnings(c):
    fields = ("multiple_entries", "invalid", "invalid_email", "revoke_invalid", "ego_user_not_found")
    counts = zero_defaults(fields, c)

    if not (counts['multiple_entries'] or counts['invalid'] or counts['invalid_email'] or counts['ego_user_notfound']):
        return ""

    report = "\n*Warnings*:\n"

    warnings = (('multiple_entries', "{} multiple entries found in configuration file"),
                ('invalid_email', "{} invalid OpenId email addresses found in configuration file"),
                ('invalid', '{}' + f" invalid users found with Cloud access but not DACO access "
                f"({counts['revoke_invalid']} had access to revoke)"),
                ('ego_user_not_found', "{} users from configuration file not found in Ego."))

    for category, message in warnings:
        try:
            if counts[category]:
                report += "\t" + message.format(counts[category]) + "\n"
        except KeyError:
            pass

    return report


def report_errors(errors):
    if not errors:
        return ''
    report = ""

    for e in errors:
        report += f"{e}\n"
    return report


def create(counts, errors, ran):
    report = "*Daco2Ego Report Summary*\n\n"
    report += report_errors(errors)
    if ran:
        report += report_warnings(counts)
        report += summarize(counts)
    return report
