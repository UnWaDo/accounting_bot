import re
from sqlalchemy.exc import IntegrityError, DBAPIError
from typing import List, Tuple, Union

INTEGRITY_PARSE = re.compile(
    r'DETAIL\:\s+Key \((?P<field>.+?)\)=\((?P<value>.+?)\) already exists')

DBAPI_PARSE = re.compile(
    r'invalid input for query argument \$(?P<number>\d+)\: (?P<value>.+?) \(')

SQL_PARSE = re.compile(r'INSERT INTO \w+? \((.*)\)')
FIELD_PARSE = re.compile(r'([\w_]+)')


class InvalidFieldsError(Exception):
    fields: List[Tuple[str, str]]

    def parse_integrity_error(self, err: IntegrityError):
        match = INTEGRITY_PARSE.search(str(err))
        if match is None:
            self.fields = []
        else:
            self.fields = [(match['field'], match['value'])]

    def parse_dbapi_error(self, err: DBAPIError):
        match = DBAPI_PARSE.search(str(err))
        if match is None or err.statement is None:
            self.fields = []
            return

        number = int(match['number'])

        sql_string = SQL_PARSE.search(err.statement)
        if sql_string is None:
            self.fields = [(f'${number}', match['value'])]
            return

        fields = FIELD_PARSE.findall(sql_string.group(1))
        self.fields = [(fields[number - 1], match['value'])]

    def __init__(self, orig: Union[IntegrityError, DBAPIError]):
        self.orig = orig

        if isinstance(orig, IntegrityError):
            self.parse_integrity_error(orig)
        else:
            self.parse_dbapi_error(orig)
