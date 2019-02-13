def summarize(c):
    fields = ("new_daco", "new_cloud", "grant_daco", "grant_cloud", "grant_both",
              "revoke_daco", "revoke_cloud", "revoke_invalid")
    counts = { k:0 for k in fields }
    counts.update(c)

    counts['new'] = counts['new_daco'] + counts['new_cloud']
    counts['grant'] = counts['grant_cloud'] + counts['grant_both']  # grants to cloud
    counts['revoke'] = counts['revoke_cloud'] + counts['revoke_invalid']  # revokes of cloud

    report = """  
*Updates*
    Added {new} new users({new_daco} with DACO access, {new_cloud} with DACO & Cloud)

    Granted DACO access to {grant_daco} existing users.
    Granted DACO and Cloud access to {grant} existing users ({grant_cloud} of them already had DACO).

    Revoked DACO access from {revoke_daco} existing users.
    Revoked DACO and Cloud access from {revoke} existing users ({revoke_invalid} of them were invalid users).
    """
    return report.format(**counts)


def report_warnings(counts):
    if not (counts['multiple_entries'] or counts['revoke_invalid'] or counts['invalid_email']):
        return ""

    report = "\n_Warnings_:\n"

    warnings=( ('multiple_entries', "{} multiple entries found in configuration file"),
               ('invalid_email',    "{} invalid OpenId email addresses found in configuration file"),
               ('revoke_invalid',   "{} invalid users found with Cloud access but not DACO access"))

    for category, message in warnings:
        try:
            if counts[category]:
                report += "\t_" + message.format(counts[category]) + "_\n"
        except KeyError:
            pass

    return report


def report_errors(errors):
    report = "*Errors*:"
    if not errors:
        return ''
    for e in errors:
        report += f"\n*{e}*"
    return report + "\n"


def create(counts, errors):
    report = "*Daco2Ego Report Summary*\n\n"
    report += report_errors(errors)
    report += report_warnings(counts)
    report += summarize(counts)
    return report

# TODO: Replace with counts generated directly by DacoClient
def count(log):
    errors = []
    counts = {"new_daco": 0,
              "new_cloud": 0,
              "grant_daco": 0,
              "grant_cloud": 0,
              "grant_both": 0,
              "revoke_daco": 0,
              "revoke_cloud": 0,
              "revoke_invalid": 0,
              "multiple_entries": 0,
              "invalid_email": 0
              }
    for line in log:
        line = line.strip()
        if line.startswith('Created user'):
            if line.endswith('cloud access'):
                counts['new_cloud'] += 1
            elif line.endswith('daco access'):
                counts['new_daco'] += 1
            else:
                print("mrap")
        elif line.startswith("Granted daco and cloud"):
            counts['grant_both'] += 1
        elif line.startswith("Granted daco"):
            counts['grant_daco'] += 1
        elif line.startswith("Granted cloud"):
            counts['grant_cloud'] += 1
        elif line.startswith("Revoked daco"):
            counts['revoke_daco'] += 1
        elif line.startswith("Revoked cloud"):
            counts['revoke_cloud'] += 1
        elif line.endswith("multiple entries in the daco file!"):
            counts['multiple_entries'] += 1
        elif line.endswith('does not have a valid email address'):
            counts['invalid_email'] += 1
        else:
            errors.append(line)

    return counts, errors