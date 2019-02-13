from requests import Session


def slack_escape(txt):
    txt = txt.replace('&', '&amp;')
    txt = txt.replace('<', '&lt;')
    txt = txt.replace('>', '&gt;')
    return txt.replace("\n", '\n')


class Reporter(object):
    def __init__(self, url):
        self.url = url
        self.session = Session()

    def send(self, report):
        headers = {'Content-type': 'application/json'}
        data = {"text": slack_escape(report), "username": "markdownbot", "mrkdwn": True}
        return self.session.post(self.url, json=data, headers=headers)
