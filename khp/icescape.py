import logging
import requests
import json

from khp import config
from khp import utils

LOG = logging.getLogger(__name__)

class Icescape():
    """Summary

    Attributes:
        headers (TYPE): Description
        password (TYPE): Description
        token (TYPE): Description
        user (TYPE): Description
        user_agent (TYPE): Description
    """

    def __init__(self):
        self.conf = config.CONFIG['icescape']
        self.user = self.conf['user']
        self.password = self.conf['password']
        self.user_agent = self.conf['user_agent']
        self.token = self._get_access_token()
        self.headers = self._build_headers()

    def _get_access_token(self):
        base_url = self.conf['login_url']
        LOG.info("Getting access token")
        r = requests.post(base_url, params={'userID': self.user,
                                            'password': self.password})
        utils.check_response(r)
        data = r.json()
        token = data['AccessToken']
        return token

    def _build_headers(self):
        headers = self.conf['headers']
        headers['Authorization'] = headers['Authorization'].format(self.token)
        return headers

    def _generate_dates(self, start_time, end_time):
        """Parse the supplied start and end times. The supplied times are
        assumed to be in the timezone specified in `config.py`.
        If none are supplied, default to yesterday. Dates are returned as a UTC
        timestamp.

        Args:
            start_time (str): Start time, accepts date formats `YYYY-mm-dd` or
                `YYYY-mm-dd H:M:S`.
            end_time (str): Start time, accepts date formats `YYYY-mm-dd`
                or `YYYY-mm-dd H:M:S`.

        Returns:
            start_time (str): start_time, as a UTC timestamp
            end_time (str): end_time, as a UTC timestamp
        """

        tz1 = config.SYS_TIMEZONE
        tz2 = config.API_TIMEZONE
        dt_format = '%Y-%m-%dT%H:%M:%S.%fZ'

        if start_time is not None and end_time is not None:
            dt1 = utils.parse_date(start_time)
            dt2 = utils.parse_date(end_time)
        else:
            dt1, dt2 = utils.yesterdays_range()
            LOG.info("Both start_time and end_time were not provided, "
                "defaulting to start: {} end: {}".format(dt1, dt2))

        dt1 = utils.convert_timezone(dt1, tz1, tz2)
        dt2 = utils.convert_timezone(dt2, tz1, tz2)
        return dt1.strftime(dt_format), dt2.strftime(dt_format)

    def get_contacts(self, interaction_type, start_time=None, end_time=None):
        """Get results from the Icescape QueryContacts2 API.

        Args:
            interaction_type (str): Type of contact (i.e. IM, Voice, Email)
            start_time (str, optional): Start time, accepts date formats
                `YYYY-mm-dd` or `YYYY-mm-dd H:M:S`. Defaults to beginning of
                yesterday.
            end_time (str, optional): Start time, accepts date formats
                `YYYY-mm-dd` or `YYYY-mm-dd H:M:S`. Defaults to end of
                yesterday.

        Returns:
            data (list): Array of contact data dictionaries
        """
        start_time, end_time = self._generate_dates(start_time, end_time)

        params = {
            'interactionTypes': interaction_type,
            'maxResults': config.MAX_RESULTS,
            'startTime': start_time,
            'endTime': end_time,
            'includeAdditionalData': True
        }
        base_url = self.conf['contacts_url']
        LOG.info("Requesting {} with params:\n{}".format(base_url, params))
        r = requests.get(base_url, params=params, headers=self.headers)
        LOG.debug("Requested: {}".format(r.url))
        utils.check_response(r)
        data = r.json()
        return data

    def get_recordings(self, contact_ids):
        """Get the results from the Icescape GetRecordings API.

        Args:
            contact_ids (list): List of Contact IDs to retrieve recordings for
        Returns:
            data (list): Array of contact data dictionaries
        """
        base_url = self.conf['recordings_url']
        payload = ["C:{}".format(contact_id) for contact_id in contact_ids]
        LOG.info("Requesting {} with payload: {}".format(base_url, payload))
        r = requests.post(base_url, data=json.dumps(payload),
                            headers=self.headers)
        utils.check_response(r)
        data = r.json()
        return data

