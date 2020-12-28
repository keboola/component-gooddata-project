# import csv
# import json
import logging
# import os
import re
import sys
from gooddata.client import GoodDataProjectClient
from gooddata.result import GoodDataWriter
from kbc.env_handler import KBCEnvHandler


KEY_USERNAME = 'username'
KEY_PASSWORD = '#password'
KEY_PROJECTID = 'projectId'
KEY_CUSTOMDOMAIN = 'customDomain'
KEY_OBJECTS = 'objects'
KEY_OBJECTS_DETAILS = 'objects_details'
KEY_GDURL = 'gooddataUrl'
KEY_DEBUG = 'debug'

MANDATORY_PARAMETERS = [KEY_USERNAME, KEY_PASSWORD, KEY_PROJECTID, KEY_OBJECTS]
QUERY_OBJECTS = ["attributes", "datasets", "facts", "folders", "metrics", "projectdashboards", "reports", "tables"]

APP_VERSION = '0.1.2'


class Writers:
    pass


class GoodDataProjectComponent(KBCEnvHandler):

    def __init__(self):

        logging.info("Running component version %s..." % APP_VERSION)

        KBCEnvHandler.__init__(self, MANDATORY_PARAMETERS)
        self.validate_config(MANDATORY_PARAMETERS)

        self.param_username = self.cfg_params[KEY_USERNAME]
        self.param_password = self.cfg_params[KEY_PASSWORD]
        self.param_project_id = self.cfg_params[KEY_PROJECTID]
        self.param_objects = self.cfg_params[KEY_OBJECTS]
        self.param_objects_details = self.cfg_params.get(KEY_OBJECTS_DETAILS, {})
        self.param_custom_domain = self.cfg_params.get(KEY_CUSTOMDOMAIN, '')
        self.param_gooddata_url = self.image_params[KEY_GDURL]

        if self.cfg_params.get('debug', False) is True:
            logger = logging.getLogger()
            logger.setLevel(level='DEBUG')

        self._processAndValidateParameters()

        self.client = GoodDataProjectClient(username=self.param_username,
                                            password=self.param_password,
                                            project_id=self.param_project_id,
                                            gooddata_url=self.param_gooddata_url)

    def _processAndValidateParameters(self):

        custDomain = re.sub(r'\s', '', self.param_custom_domain)

        if custDomain != '':

            rxgString = r'https://.*\.gooddata\.com/*'
            rgxCheck = re.fullmatch(rxgString, custDomain)

            if rgxCheck is None:
                logging.error(f"{custDomain} is not a valid GoodData domain.")
                sys.exit(1)

            else:
                self.param_gooddata_url = custDomain

        logging.info(f"Using domain {self.param_gooddata_url}.")

    def downloadAllData(self):

        for obj, value in self.param_objects.items():

            if value is False:
                continue

            if obj == 'users':
                logging.info("Downloading data about users.")

                _wrt = GoodDataWriter(self.tables_out_path, 'users', False)
                _all_users = [x['user'] for x in self.client.getAllUsers()]
                _wrt.writerows(_all_users)

            if obj == 'usergroups':
                logging.info("Downloading info about user groups.")

                _wrt = GoodDataWriter(self.tables_out_path, 'usergroups', False)
                _all_usergroups = self.client.getUserGroups(self.param_project_id)

                ug_prep = [ug['userGroup'] for ug in _all_usergroups]

                for ug in ug_prep:
                    ug['project_id'] = ug['content']['project'].split('/')[-1]
                _wrt.writerows(ug_prep)

                _ug_ids = [ug['userGroup']['content']['id'] for ug in _all_usergroups]
                _wrt_members = GoodDataWriter(self.tables_out_path, 'usergroups-members', False)

                for ug in _ug_ids:
                    _ug_members = self.client.getUserGroupMembers(ug)
                    mem_prep = [u['user'] for u in _ug_members]

                    for mem in mem_prep:
                        mem['user_id'] = mem['links']['self'].split('/')[-1]
                        mem['usergroup_id'] = ug

                    _wrt_members.writerows(mem_prep)

            elif obj in QUERY_OBJECTS:
                logging.info(f"Downloading metadata for object type {obj}")

                _wrt = GoodDataWriter(self.tables_out_path, obj, False, result_type='md')
                _all_objects = self.client.queryObjects(obj)
                _wrt.writerows(_all_objects)

                if self.param_objects_details.get(obj, False) is True:
                    logging.info(f"Downloading details for all objects of type {obj}.")

                    _wrt_detail = GoodDataWriter(self.tables_out_path, str(obj) + '_details', False, 'detail')
                    details = []
                    for md in _all_objects:
                        link = md['link']
                        idf = md['identifier']
                        _detail = self.client.getObjectDetail(link)
                        details += [{'link': link, 'identifier': idf, 'type': obj, 'detail': _detail}]

                    _wrt_detail.writerows(details)

            else:
                pass

    def run(self):

        self.downloadAllData()
