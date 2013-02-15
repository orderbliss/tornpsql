#!/usr/bin/env python
#
# Copyright 2013 Facebook
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

import itertools
import logging
import os

import psycopg2


version = "0.1"
version_info = (0, 1, 0, 0)

class Connection(object):
	"""A lightweight wrapper around PostgreSQL DB-API connections.
	"""
	def __init__(self, host, database, user=None, password=None, port=5432):
		self.host = host
		self.database = database
		self.logging = False
		args = dict(host=host, database=database, port=port, 
			user=user, password=password)

		self._db = None
		self._db_args = args
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

	def query(self, query, parameters=None, **kwargs):
		"""Returns a row list for the given query and parameters."""
		cursor = self._cursor()
		try:
			self._execute(cursor, query, parameters)	
			if cursor.description:
				column_names = [column.name for column in cursor.description]
				return [Row(itertools.izip(column_names, row)) for row in cursor.fetchall()]
		finally:
			cursor.close()
	
	def execute(self, query, parameters=None, **kwargs):
		return self.query(query, parameters, **kwargs)

	def get(self, query, parameters):
		"""Returns the first row returned for the given query."""
		rows = self.query(query, parameters)
		if not rows:
			return None
		elif len(rows) > 1:
			raise Exception("Multiple rows returned for Database.get() query")
		else:
			return rows[0]


	def executemany(self, query, parameters, **kwargs):
		"""Executes the given query against all the given param sequences.
		"""
		cursor = self._cursor()
		try:
			self._executemany(query, parameters, **kwargs)
			return True
		finally:
			cursor.close()
			return False
	
	def execute_rowcount(self, query, parameters):
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
			if self.logging:
				logging.info(cursor.mogrify(query, parameters if type(parameters) is tuple else (parameters, )))
			cursor.execute(query, parameters if type(parameters) is tuple else (parameters, ))
		except psycopg2.OperationalError as e:
			logging.error("Error connecting to PostgreSQL on %s, %s", self.host, e)
			self.close()
			raise
	
	def _executemany(self, cursor, query, parameters):
		try:
			if self.logging:
				logging.info(cursor.mogrify(query, parameters if type(parameters) is list else [parameters]))
			cursor.executemany(query, parameters if type(parameters) is list else [parameters])
		except psycopg2.OperationalError as e:
			logging.error("Error connecting to PostgreSQL on %s, e", self.host, e)
			self.close()
			raise 
	

class Row(dict):
	"""A dict that allows for object-like property access syntax."""
	def __getattr__(self, name):
		try:
			return self[name]
		except KeyError:
			raise AttributeError(name)