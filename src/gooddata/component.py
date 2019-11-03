import csv
import json
import logging
import os
import re
import sys
from gooddata.client import GoodDataProjectClient
from kbc.env_handler import KBCEnvHandler


KEY_USERNAME = 'username'
KEY_PASSWORD = '#password'
KEY_PROJECTID = 'projectId'
KEY_CUSTOMDOMAIN = 'customDomain'
KEY_GDURL = 'gooddataUrl'

MANDATORY_PARAMETERS = [KEY_USERNAME, KEY_PASSWORD, KEY_PROJECTID]

FIELD_USERS = ['login', 'firstname', 'lastname', 'email', 'phonenumber',
               'userRoles', 'status', 'uri', 'created', 'updated']


class GoodDataProjectComponent(KBCEnvHandler):

    def __init__(self):

        KBCEnvHandler.__init__(self, MANDATORY_PARAMETERS)
        self.validate_config(MANDATORY_PARAMETERS)

        self.paramUsername = self.cfg_params[KEY_USERNAME]
        self.paramPassword = self.cfg_params[KEY_PASSWORD]
        self.paramProjectId = self.cfg_params[KEY_PROJECTID]
        self.paramCustomDomain = self.cfg_params[KEY_CUSTOMDOMAIN]
        self.paramGooddataUrl = self.image_params[KEY_GDURL]

        self._processAndValidateParameters()

        self.client = GoodDataProjectClient(username=self.paramUsername,
                                            password=self.paramPassword,
                                            projectId=self.paramProjectId,
                                            baseGoodDataUrl=self.paramGooddataUrl)

        self.writer = csv.DictWriter(open(os.path.join(self.tables_out_path, 'users.csv'), 'w'),
                                     fieldnames=FIELD_USERS, extrasaction='ignore', restval='',
                                     quotechar='\"', quoting=csv.QUOTE_ALL)
        self.writer.writeheader()

    def _processAndValidateParameters(self):

        custDomain = re.sub(r'\s', '', self.paramCustomDomain)

        if custDomain != '':

            rxgString = r'https://.*\.gooddata\.com/*'
            rgxCheck = re.fullmatch(rxgString, custDomain)

            if rgxCheck is None:

                logging.error("%s is not a valid GoodData domain." %
                              custDomain)
                sys.exit(1)

            else:

                self.paramGooddataUrl = custDomain

        logging.info("Using domain %s." % self.paramGooddataUrl)

    def getUsers(self):

        allUsers = self.client.getAllUsers()

        for u in allUsers:

            _outDict = {}
            _outDict['login'] = u['user']['content']['login']
            _outDict['firstname'] = u['user']['content']['firstname']
            _outDict['lastname'] = u['user']['content']['lastname']
            _outDict['email'] = u['user']['content']['email']
            _outDict['phonenumber'] = u['user']['content']['phonenumber']
            _outDict['userRoles'] = json.dumps(u['user']['content']['userRoles'])
            _outDict['status'] = u['user']['content']['status']
            _outDict['uri'] = u['user']['links']['self']
            _outDict['created'] = u['user']['meta']['created']
            _outDict['updated'] = u['user']['meta']['updated']

            self.writer.writerow(_outDict)

    def run(self):

        self.getUsers()
