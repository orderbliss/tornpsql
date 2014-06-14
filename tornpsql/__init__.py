#!/usr/bin/env python
import re
import os
import logging
import psycopg2
import itertools
import psycopg2.extras
from psycopg2.extensions import adapt

# http://initd.org/psycopg/docs/module.html#exceptions
from psycopg2 import Warning
from psycopg2 import Error
from psycopg2 import InterfaceError
from psycopg2 import DatabaseError
from psycopg2 import DataError
from psycopg2 import OperationalError
from psycopg2 import IntegrityError
from psycopg2 import InternalError
from psycopg2 import ProgrammingError
from psycopg2 import NotSupportedError


__version__ = VERSION = version = '0.2.1'

from .pubsub import PubSub


class Connection(object):
    def __init__(self, host_or_url=None, database=None, user=None, password=None, port=5432, search_path=None, timezone="+00"):
        self.logging = False
        if host_or_url is None:
            host_or_url = os.getenv('TORNPSQL', "127.0.0.1")
        if host_or_url.startswith('postgres://'):
            try:
                args = re.search('postgres://(?P<user>[\w\-]*):?(?P<password>[\w\-]*)@(?P<host>[\w\-\.]+):?(?P<port>\d+)/?(?P<database>[\w\-]+)', host_or_url).groupdict()
            except:
                raise ValueError("PostgreSQL url is not a valid format postgres://user:password@host:post/database from %s" % host_or_url)
            else:
                self.host = args.get('host')
                self.database = args.get('database')
        else:
            self.host = host_or_url
            self.database = database
            args = dict(host=host_or_url, database=database, port=int(port), 
                        user=user, password=password)

        self.timezone = timezone
        self._db = None
        self._db_args = args
        self._register_types = []
        self._search_path = search_path or "public"
        self._change_path = None
        try:
            self.reconnect()
        except Exception: # pragma: no cover
            logging.error("Cannot connect to PostgreSQL on postgresql://%s:<password>@%s/%s", 
                args['user'], self.host, self.database, exc_info=True)

    def __del__(self):
        self.close()

    def close(self):
        """Closes this database connection."""
        if getattr(self, "_db", None) is not None:
            self._db.close()
            self._db = None

    def reconnect(self):
        """Closes the existing database connection and re-opens it."""
        self.close()
        self._db = psycopg2.connect(**self._db_args)
        self._db.autocommit = True

        psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)

        # register custom types
        for _type in self._register_types:
            psycopg2.extensions.register_type(psycopg2.extensions.new_type(*_type))

        try:
            psycopg2.extras.register_hstore(self._db, globally=True)
        except psycopg2.ProgrammingError: # pragma: no cover
            pass

    def path(self, search_path):
        self._change_path = search_path
        return self

    def adapt(self, value):
        return adapt(value)

    def register_type(self, oids, name, casting):
        """Callback to register data types when reconnect
        """
        assert type(oids) is tuple
        assert type(name) in (unicode, str)
        assert hasattr(casting, "__call__")
        self._register_types.append((oids, name, casting))
        psycopg2.extensions.register_type(psycopg2.extensions.new_type(oids, name, casting))

    def mogrify(self, query, *parameters, **kwargs):
        """From http://initd.org/psycopg/docs/cursor.html?highlight=mogrify#cursor.mogrify
        Return a query string after arguments binding.
        The string returned is exactly the one that would be sent to the database running 
        the execute() method or similar.
        """
        cursor = self._cursor()
        try:
            if kwargs:
                return cursor.mogrify(query % dict(map(lambda r: (r[0], adapt(r[1])), kwargs.items())))
            return cursor.mogrify(query, parameters)
        except: # pragma: no cover
            cursor.close()
            raise

    def query(self, query, *parameters, **kwargs):
        """Returns a row list for the given query and parameters."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters, kwargs)    
            if cursor.description:
                column_names = [column.name for column in cursor.description]
                return [Row(itertools.izip(column_names, row)) for row in cursor.fetchall()]
        except:
            cursor.close()
            raise

    def execute(self, query, *parameters):
        """Alias for query"""
        return self.query(query, *parameters)

    def get(self, query, *parameters, **kwargs):
        """Returns the first row returned for the given query."""
        rows = self.query(query, *parameters, **kwargs)
        if not rows:
            return None
        elif len(rows) > 1:
            raise ValueError("Multiple rows returned for get() query")
        else:
            return rows[0]

    def executemany(self, query, *parameters):
        """Executes the given query against all the given param sequences.
        """
        cursor = self._cursor()
        try:
            self._executemany(cursor, query, parameters)
        except Exception: # pragma: no cover
            cursor.close()
            raise

    def _ensure_connected(self):
        if self._db is None:
            self.reconnect()

    def _cursor(self):
        self._ensure_connected()
        return self._db.cursor()

    def _set_search_path(self, query):
        if self._change_path and not re.search(r'^set search_path', query, re.I):
            query = ("set search_path = %s;" % self._change_path) + query
            self._change_path = None
        elif self._search_path and not re.search(r'^set search_path', query, re.I):
            query = ("set search_path = %s;" % self._search_path) + query
        if self.timezone:
            query = ("set timezone = '%s';" % self.timezone) + query
        return query

    def _execute(self, cursor, query, parameters, kwargs):
        try:
            query = self._set_search_path(query)
            if self.logging: 
                logging.info(re.sub(r"\n\s*", " ", cursor.mogrify(query, *parameters, **kwargs)))

            if kwargs:
                cursor.execute(query % dict(map(lambda r: (r[0], adapt(r[1])), kwargs.items())))
            else:
                cursor.execute(query, parameters)

        except psycopg2.OperationalError as e: # pragma: no cover
            logging.error("Error connecting to PostgreSQL on %s, %s", self.host, e)
            self.close()
            raise

    def _executemany(self, cursor, query, parameters):
        """The function is mostly useful for commands that update the database: 
           any result set returned by the query is discarded."""
        try:
            query = self._set_search_path(query)
            cursor.executemany(query, parameters)
        except psycopg2.OperationalError as e: # pragma: no cover
            logging.error("Error connecting to PostgreSQL on %s, e", self.host, e)
            self.close()
            raise 

    def pubsub(self):
        return PubSub(self._db)

    def file(self, path, _execute=True):
        base = os.path.dirname(path)
        with open(path) as r:
            sql = re.sub(r'\\ir\s(.*)', lambda m: self.file(os.path.join(base, m.groups()[0]), False), r.read())
        if _execute:
            cursor = self._cursor()
            if self._change_path:
                sql = ("set search_path = %s;" % self._change_path) + sql
                self._change_path = None
            elif self._search_path:
                sql = ("set search_path = %s;" % self._search_path) + sql
            return cursor.execute(sql)
        else:
            return sql

    @property
    def notices(self):
        """pops and returns all notices
        http://initd.org/psycopg/docs/connection.html#connection.notices
        """
        return [self._db.notices.pop()[8:].strip() for x in range(len(self._db.notices))]

class Row(dict):
    """A dict that allows for object-like property access syntax."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:  # pragma: no cover
            raise AttributeError(name)
