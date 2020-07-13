import os
import csv
import json

FIELDS_METADATA = ['identifier', 'link', 'locked', 'author', 'tags', 'created', 'updated', 'deprecated', 'summary',
                   'isProduction', 'title', 'category', 'unlisted', 'contributor']
FIELDS_R_METADATA = ['identifier', 'uri', 'locked', 'author', 'tags', 'created', 'updated', 'deprecated', 'summary',
                     'is_production', 'title', 'category', 'unlisted', 'contributor']
PK_METADATA = ['identifier', 'uri']
DONOTFLATTEN_METADATA = []
FORCETYPE_METADATA = []

FIELDS_USERS = ['content_login', 'content_firstname', 'content_lastname', 'content_email',
                'content_phonenumber', 'content_userRoles', 'content_status', 'links_self',
                'meta_created', 'meta_updated']
FIELDS_R_USERS = ['login', 'firstname', 'lastname', 'email', 'phonenumber', 'userRoles', 'status',
                  'uri', 'created', 'updated']
PK_USERS = ['login']
DONOTFLATTEN_USERS = []
FORCETYPE_USERS = ['content_userRoles']

FIELDS_DETAIL = ['identifier', 'link', 'type', 'detail']
FIELDS_R_DETAIL = ['identifier', 'uri', 'type', 'detail']
PK_DETAIL = ['identifier', 'uri']
DONOTFLATTEN_DETAIL = ['detail']
FORCETYPE_DETAIL = []


class GoodDataWriter:

    def __init__(self, tableOutPath, tableName, incremental, result_type=None):

        self.paramPath = tableOutPath
        self.paramTableName = tableName
        self.paramTable = tableName + '.csv'
        self.paramTablePath = os.path.join(self.paramPath, self.paramTable)
        self.paramIncremental = incremental

        if result_type == 'md':
            self.paramFields = FIELDS_METADATA
            self.paramJsonFields = DONOTFLATTEN_METADATA
            self.paramPrimaryKey = PK_METADATA
            self.paramFieldsRenamed = FIELDS_R_METADATA
            self.paramForceType = FORCETYPE_METADATA

        elif result_type == 'detail':
            self.paramFields = FIELDS_DETAIL
            self.paramJsonFields = DONOTFLATTEN_DETAIL
            self.paramPrimaryKey = PK_DETAIL
            self.paramFieldsRenamed = FIELDS_R_DETAIL
            self.paramForceType = FORCETYPE_DETAIL

        else:
            self.paramFields = eval(f'FIELDS_{tableName.upper().replace("-", "_")}')
            self.paramJsonFields = eval(f'DONOTFLATTEN_{tableName.upper().replace("-", "_")}')
            self.paramPrimaryKey = eval(f'PK_{tableName.upper().replace("-", "_")}')
            self.paramFieldsRenamed = eval(f'FIELDS_R_{tableName.upper().replace("-", "_")}')
            self.paramForceType = eval(f'FORCETYPE_{tableName.upper().replace("-", "_")}')

        self.createManifest()
        self.createWriter()

    def createManifest(self):

        template = {
            'incremental': self.paramIncremental,
            'primary_key': self.paramPrimaryKey,
            'columns': self.paramFieldsRenamed
        }

        path = self.paramTablePath + '.manifest'

        with open(path, 'w') as manifest:
            json.dump(template, manifest)

    def createWriter(self):

        self.writer = csv.DictWriter(open(self.paramTablePath, 'w'), fieldnames=self.paramFields,
                                     restval='', extrasaction='ignore', quotechar='\"', quoting=csv.QUOTE_ALL)

    def writerows(self, listToWrite, parentDict=None):

        for row in listToWrite:

            row_f = self.flatten_json(x=row)

            if self.paramJsonFields != []:
                for field in self.paramJsonFields:
                    row_f[field] = json.dumps(row[field])

            _dictToWrite = {}

            for key, value in row_f.items():

                if key in self.paramFields:
                    if key in self.paramForceType:
                        _dictToWrite[key] = json.dumps(value)
                    else:
                        _dictToWrite[key] = value

                else:
                    continue

            if parentDict is not None:
                _dictToWrite = {**_dictToWrite, **parentDict}

            self.writer.writerow(_dictToWrite)

    def flatten_json(self, x, out=None, name=''):
        non_flattened = dict()
        if out is None:
            out = dict()

        if type(x) is dict:
            for a in x:
                if a in self.paramJsonFields:
                    non_flattened[a] = x[a]
                else:
                    self.flatten_json(x[a], out, name + a + '_')
        else:
            out[name[:-1]] = x

        return {**out, **non_flattened}
