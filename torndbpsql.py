#!/usr/bin/env python
#
# Copyright 2013 Steve Peak
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A lightweight wrapper around PostgreSQL.
Forked from http://github.com/bdarnell/torndb
"""

from __future__ import absolute_import, division, with_statement

import copy
import itertools
import logging
import os
import time

try:
    import psycopg2
except ImportError:
    # If psycopg2 isn't available this module won't actually be useable,
    # but we want it to at least be importable on readthedocs.org,
    # which has limitations on third-party modules.
    if 'READTHEDOCS' in os.environ:
        psycopg2 = None
    else:
        raise

version = "0.1"
version_info = (0, 1, 0, 0)

class Connection(object):
	"""A lightweight wrapper around PostgreSQL DB-API connections.
	"""
	def __init__(self, host, database, user=None, password=None, port=5432,
			max_idle_time=7 * 3600, time_zone="+0:00"):
		self.host = host
		self.database = database
		self.max_idle_time = max_idle_time

		args = dict(dbname=database, port=port, 
			user=user, password=password)

		# We accept a path to a MySQL socket file or a host(:port) string
		self._db = None
		self._db_args = args
		self._last_use_time = time.time()
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

	def iter(self, query, *parameters):
		"""Returns an iterator for the given query and parameters."""
		self._ensure_connected()
		cursor = self._db.cursor()
		try:
			self._execute(cursor, query, parameters)
			column_names = [column.name for column in cursor.description]
			for row in cursor.fetchall():
				yield Row(zip(column_names, row))
		finally:
			cursor.close()

	def query(self, query, *parameters):
		"""Returns a row list for the given query and parameters."""
		cursor = self._cursor()
		try:
			self._execute(cursor, query, parameters)
			column_names = [column.name for column in cursor.description]
			return [Row(itertools.izip(column_names, row)) for row in cursor.fetchall()]
		finally:
			cursor.close()

	def get(self, query, *parameters):
		"""Returns the first row returned for the given query."""
		rows = self.query(query, *parameters)
		if not rows:
			return None
		elif len(rows) > 1:
			raise Exception("Multiple rows returned for Database.get() query")
		else:
			return rows[0]

	# rowcount is a more reasonable default return value than lastrowid,
	# but for historical compatibility execute() must return lastrowid.
	def execute(self, query, *parameters):
		"""Executes the given query, returning the lastrowid from the query."""
		return self.execute_lastrowid(query, *parameters)

	def executemany(self, query, parameters):
		"""Executes the given query against all the given param sequences.
		"""
		cursor = self._cursor()
		try:
			self._executemany(query, parameters)
			return True
		finally:
			cursor.close()
			return False
	
	def execute_rowcount(self, query, *parameters):
		"""Executes the given query, returning the rowcount from the query."""
		cursor = self._cursor()
		try:
			self._execute(cursor, query, parameters)
			return cursor.rowcount
		finally:
			cursor.close()

	def _ensure_connected(self):
		# Mysql by default closes client connections that are idle for
		# 8 hours, but the client library does not report this fact until
		# you try to perform a query and it fails.  Protect against this
		# case by preemptively closing and reopening the connection
		# if it has been idle for too long (7 hours by default).
		if (self._db is None or
			(time.time() - self._last_use_time > self.max_idle_time)):
			self.reconnect()
		self._last_use_time = time.time()

		def _cursor(self):
			self._ensure_connected()
			return self._db.cursor()

	def _execute(self, cursor, query, parameters):
		try:
			return cursor.execute(query, parameters)
		except OperationalError:
			logging.error("Error connecting to MySQL on %s", self.host)
			self.close()
			raise
	
	def _executemany(self, cursor, query, parameters):
		try:
			cursor.executemany(query, parameters)
		except OperationalError:
			logging.error("Error connecting to MySQL on %s", self.host)
			self.close()
			raise 
	

class Row(dict):
	"""A dict that allows for object-like property access syntax."""
	def __getattr__(self, name):
		try:
			return self[name]
		except KeyError:
			raise AttributeError(name)