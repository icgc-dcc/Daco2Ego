import json
import logging
from oauthlib.oauth2 import TokenExpiredError


def retry_oauth(func):
    """
    Decorator for methods making rest requests
    Retry the request if encountering a TokenExpiredError by generating a new rest client with a new OAuth2 Bearer Token
    :param func: function to decorate
    :return: decorated function
    """

    def func_wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except TokenExpiredError as e:
            logging.info('Token expired for Daco2Ego, requesting new authorization.')
            if self._rest_client_factory is not None:
                self._rest_client = self._rest_client_factory()
                return func(self, *args, **kwargs)
            else:
                raise e

    return func_wrapper


class DacoV2EgoClient(object):
    def __init__(self, ego_url, rest_client, dac_api_url, rest_client_factory=None):
        logging.info("daco v2 ego client initializing")
        self.ego_url = ego_url
        self.dac_api_url = dac_api_url

        self._rest_client_factory = rest_client_factory  # Function to produce new rest client if needed to re-auth
        self._rest_client = rest_client
        self._rest_client.stream = False

    @retry_oauth
    def _get(self, endpoint):
        r = self._rest_client.get(self.ego_url + endpoint)
        if r.ok:
            return r.text
        raise IOError(f"Error trying to GET {r.url}", r)

    @retry_oauth
    def download_daco2_approved_users(self):
        r = self._rest_client.get(self.dac_api_url + "/export/approved-users/?format=daco-file-format")
        
        if r.ok:
            return r.text
        raise IOError(f"Error requesting approved users from {r.url}", r)