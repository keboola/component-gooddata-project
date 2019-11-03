import json
import logging
import os
import sys
from kbc.client_base import HttpClientBase


class GoodDataProjectClient(HttpClientBase):

    def __init__(self, username, password, projectId, baseGoodDataUrl):

        self.paramUsername = username  # don't forget to lower this
        self.paramPassword = password
        self.paramProjectId = projectId
        self.paramBaseGoodDataUrl = baseGoodDataUrl

        HttpClientBase.__init__(
            self, base_url=self.paramBaseGoodDataUrl, max_retries=10)

        self._getSstToken()

    def _getSstToken(self):

        reqHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        reqBody = json.dumps({
            "postUserLogin": {
                "login": self.paramUsername,
                "password": self.paramPassword,
                "remember": 1,
                "verify_level": 2
            }
        })

        reqUrl = os.path.join(self.base_url, 'gdc/account/login')

        respObj = self.post_raw(url=reqUrl, headers=reqHeaders, data=reqBody)
        respSc, respJs = respObj.status_code, respObj.json()

        if respSc == 200:

            self.varSstToken = respJs['userLogin']['token']
            logging.info("SST token obtained.")

        else:

            logging.error("Could not obtain SST token.")
            logging.error("Received: %s - %s." % (respSc, respJs))
            sys.exit(1)

    def _getTtToken(self):

        reqHeaders = {
            'Accept': 'application/json',
            'X-GDC-AuthSST': self.varSstToken
        }

        reqUrl = os.path.join(self.base_url, 'gdc/account/token')

        respObj = self.get_raw(url=reqUrl, headers=reqHeaders)
        respSc, respJs = respObj.status_code, respObj.json()

        if respSc == 200:

            self.varTtToken = respJs['userToken']['token']

        else:

            logging.error("There was an error, when obtaining TT token.")
            logging.error("Received: %s - %s" % (respSc, respJs))
            sys.exit(2)

    def _buildHeader(self):

        self._getTtToken()

        _headerTemplate = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-GDC-AuthTT': self.varTtToken
        }

        self.reqHeader = _headerTemplate

    def getAllUsers(self):

        self._buildHeader()

        urlUsers = os.path.join(self.paramBaseGoodDataUrl, f'gdc/projects/{self.paramProjectId}/users')
        reqUsers = self.get_raw(urlUsers, headers=self.reqHeader)
        scUsers, jsUsers = reqUsers.status_code, reqUsers.json()

        if scUsers == 200:

            logging.info("Users extracted.")
            return jsUsers['users']

        else:

            logging.error("Could not obtain users.")
            sys.exit(1)
