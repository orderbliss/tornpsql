#!/usr/bin/env python
import re
import os
import logging
import psycopg2
import itertools
import psycopg2.extras
from decimal import Decimal

__version__ = VERSION = version = '0.2.0'

from .pubsub import PubSub

class Connection(object):
    def __init__(self, host_or_url="127.0.0.1", database=None, user=None, password=None, port=5432, search_path=None):
        self.logging = False
        if host_or_url.startswith('postgres://'):
            args = re.search('postgres://(?P<user>[\w\-]*):?(?P<password>[\w\-]*)@(?P<host>[\w\-\.]+):?(?P<port>\d+)/?(?P<database>[\w\-]+)', host_or_url).groupdict()
            self.host = args.get('host')
            self.database = args.get('database')
        else:
            self.host = host_or_url
            self.database = database
            args = dict(host=host_or_url, database=database, port=int(port), 
                        user=user, password=password)

        self._db = None
        self._db_args = args
        self._register_types = []
        self._search_path = search_path
        self._change_path = None
        try:
            self.reconnect()
        except Exception:
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

        # register money type
        psycopg2.extensions.register_type(psycopg2.extensions.new_type((790,), "MONEY", self._cast_money))

        # register custom types
        for _type in self._register_types:
            psycopg2.extensions.register_type(psycopg2.extensions.new_type(*_type))

        try:
            psycopg2.extras.register_hstore(self._db, globally=True)
        except psycopg2.ProgrammingError:
            pass

    def path(self, search_path):
        self._change_path = search_path
        return self

    def hstore(self, dict):
        return ','.join(['"%s"=>"%s"' % (str(k), str(v)) for k, v in dict.items()])

    def _cast_money(self, s, cur):
        if s is None:
            return None
        return Decimal(s.replace(",","").replace("$",""))

    def register_type(self, oids, name, casting):
        """Callback to register data types when reconnect
        """
        assert type(oids) is tuple
        assert type(name) in (unicode, str)
        assert hasattr(casting, "__call__")
        self._register_types.append((oids, name, casting))
        if self._db is not None:
            psycopg2.extensions.register_type(psycopg2.extensions.new_type(oids, name, casting))

    def mogrify(self, query, *parameters):
        """From http://initd.org/psycopg/docs/cursor.html?highlight=mogrify#cursor.mogrify
        Return a query string after arguments binding.
        The string returned is exactly the one that would be sent to the database running 
        the execute() method or similar.
        """
        cursor = self._cursor()
        try:
            return cursor.mogrify(query, parameters)
        except:
            cursor.close()
            raise

    def query(self, query, *parameters):
        """Returns a row list for the given query and parameters."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters)    
            if cursor.description:
                column_names = [column.name for column in cursor.description]
                return [Row(itertools.izip(column_names, row)) for row in cursor.fetchall()]
        except:
            cursor.close()
            raise

    def execute(self, query, *parameters):
        """Alias for query"""
        return self.query(query, *parameters)

    def get(self, query, *parameters):
        """Returns the first row returned for the given query."""
        rows = self.query(query, *parameters)
        if not rows:
            return None
        elif len(rows) > 1:
            raise Exception("Multiple rows returned for Database.get() query")
        else:
            return rows[0]

    def executemany(self, query, *parameters):
        """Executes the given query against all the given param sequences.
        """
        cursor = self._cursor()
        try:
            self._executemany(cursor, query, parameters)
            return True
        except Exception:
            cursor.close()
            raise

    def execute_rowcount(self, query, *parameters):
        """Executes the given query, returning the rowcount from the query."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters)
            return cursor.rowcount
        finally:
            cursor.close()

    def _ensure_connected(self):
        if self._db is None:
            self.reconnect()

    def _cursor(self):
        self._ensure_connected()
        return self._db.cursor()

    def _execute(self, cursor, query, parameters):
        try:
            if self._change_path and not re.search(r'set search_path', query, re.I):
                query = ("set search_path = %s;" % self._change_path) + query
                self._change_path = None
            elif self._search_path and not re.search(r'set search_path', query, re.I):
                query = ("set search_path = %s;" % self._search_path) + query
            if self.logging:
                logging.info(cursor.mogrify(query, parameters))
            cursor.execute(query, parameters)
        except psycopg2.OperationalError as e:
            logging.error("Error connecting to PostgreSQL on %s, %s", self.host, e)
            self.close()
            raise

    def _executemany(self, cursor, query, parameters):
        """The function is mostly useful for commands that update the database: any result set returned by the query is discarded."""
        try:
            if self._change_path and not re.search(r'set search_path', query, re.I):
                query = ("set search_path = %s;" % self._change_path) + query
                self._change_path = None
            elif self._search_path and not re.search(r'set search_path', query, re.I):
                query = ("set search_path = %s;" % self._search_path) + query
            if self.logging:
                logging.info(cursor.mogrify(query, parameters))
            cursor.executemany(query, parameters)
        except psycopg2.OperationalError as e:
            logging.error("Error connecting to PostgreSQL on %s, e", self.host, e)
            self.close()
            raise 

    def pubsub(self):
        return PubSub(self._db)

    def file(self, path, execute=True):
        base = os.path.dirname(path)
        with open(path) as r:
            sql = re.sub(r'\\ir\s(.*)', lambda m: self.file(os.path.join(base, m.groups()[0]), False), r.read(), re.M)
        if execute:
            cursor = self._cursor()
            cursor.execute(sql)
        else:
            return sql



class Row(dict):
    """A dict that allows for object-like property access syntax."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)
