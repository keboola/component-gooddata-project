import json
import logging
import sys
import requests
from kbc.client_base import HttpClientBase
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin


class GoodDataProjectClient(HttpClientBase):

    def __init__(self, username, password, project_id, gooddata_url):

        self.param_username = username
        self.param_password = password
        self.param_pid = project_id
        self.param_gooddata_url = gooddata_url

        _def_header = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        HttpClientBase.__init__(self, base_url=self.param_gooddata_url, max_retries=10,
                                default_http_header=_def_header)

        self._getSstToken()
        self._auth_header['X-GDC-AuthTT'] = self._getTtToken()

    def _getSstToken(self):

        body_sst = json.dumps({
            "postUserLogin": {
                "login": self.param_username,
                "password": self.param_password,
                "remember": 1,
                "verify_level": 2
            }
        })

        url_sst = urljoin(self.base_url, '/gdc/account/login')

        rsp_sst = self.post_raw(url=url_sst, data=body_sst)
        sc_sst, js_sst = rsp_sst.status_code, rsp_sst.json()

        if sc_sst == 200:
            self.varSstToken = js_sst['userLogin']['token']
            logging.info("SST token obtained.")

        else:
            logging.error("Could not obtain SST token.")
            logging.error("Received: %s - %s." % (sc_sst, js_sst))
            sys.exit(1)

    def _getTtToken(self):

        url_tt = urljoin(self.base_url, '/gdc/account/token')
        hdr_tt = {'X-GDC-AuthSST': self.varSstToken}

        rsp_tt = self.get_raw(url=url_tt, headers=hdr_tt)
        sc_tt, js_tt = rsp_tt.status_code, rsp_tt.json()

        if sc_tt == 200:
            self.varTtToken = js_tt['userToken']['token']
            return self.varTtToken

        else:
            logging.error("There was an error, when obtaining TT token.")
            logging.error("Received: %s - %s" % (sc_tt, js_tt))
            sys.exit(2)

    def __response_hook(self, res, *args, **kwargs):
        if res.status_code == 401:
            token = self._getTtToken()
            self._auth_header = {"X-GDC-AuthTT": token,
                                 "Accept": "application/json",
                                 "Content-Type": "application/json"}

            res.request.headers['X-GDC-AuthTT'] = token
            s = requests.Session()
            return self.requests_retry_session(session=s).send(res.request)

    def requests_retry_session(self, session=None):

        session = session or requests.Session()
        retry = Retry(
            total=self.max_retries,
            read=self.max_retries,
            connect=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=self.status_forcelist,
            method_whitelist=('GET', 'POST', 'PATCH', 'UPDATE', 'DELETE')
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        # append response hook
        session.hooks['response'].append(self.__response_hook)
        return session

    def getAllUsers(self):

        url_users = urljoin(self.param_gooddata_url, f'gdc/projects/{self.param_pid}/users')
        rsp_users = self.get_raw(url_users)
        sc_users, js_users = rsp_users.status_code, rsp_users.json()

        if sc_users == 200:
            return js_users['users']

        else:
            logging.error(f"Could not obtain users. Received: {sc_users} - {js_users}.")
            sys.exit(1)

    def queryObjects(self, object_type):

        url_query = urljoin(self.param_gooddata_url, f'gdc/md/{self.param_pid}/query/{object_type}')
        rsp_query = self.get_raw(url=url_query)
        sc_query, js_query = rsp_query.status_code, rsp_query.json()

        if sc_query == 200:
            return js_query['query']['entries']

        else:
            logging.error(f"Could not query object type {object_type}. Received: {sc_query} - {js_query}.")
            sys.exit(1)

    def getObjectDetail(self, object_url):

        url_object = urljoin(self.param_gooddata_url, object_url)
        rsp_object = self.get_raw(url=url_object)
        sc_object, js_object = rsp_object.status_code, rsp_object.json()

        if sc_object == 200:
            return js_object

        else:
            logging.error(f"Could not download details for object {object_url}. Received: {sc_object} - {js_object}.")
            sys.exit(1)
