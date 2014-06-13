import os
import unittest
import tornpsql
from decimal import Decimal

from psycopg2.extras import HstoreAdapter

class tornpsqlTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        try:
            self.db = tornpsql.Connection()
        except:
            pass

    def test_a_file(self):
        "can execute from file"
        self.db.file(os.path.join(os.path.dirname(__file__), "test.sql"))
        self.assertEqual(self.db.get("SELECT count(*) c from public.users;").c, 10)

    def test_connection_args(self):
        "test connect with args"
        db = tornpsql.Connection("127.0.0.1", "tornpsql", os.getenv("postgres", None))
        self.assertTrue(db.get("select true as connected").connected)

    def test_registering_type(self):
        self.skipTest("wip")
        self.db.register_type()

    def test_mogrify(self):
        "can mogrify w/ inline args"
        self.assertEqual(self.db.mogrify("select true from user where email=%s;", "joe@smoe.com"),
                         "select true from user where email='joe@smoe.com';")

    def test_mogrify_dict(self):
        "can mogrify w/ dict args"
        self.assertEqual(self.db.mogrify("select true from user where email=%(email)s;", email="joe@smoe.com"),
                         "select true from user where email='joe@smoe.com';")
    
    def test_connection_from_url(self):
        "can connect from the os.getenv('TORNPSQL')"
        db = tornpsql.Connection()
        self.assertTrue(db.get("select true as connected").connected)

    def test_adapting(self):
        "can adapt data types outside query"
        self.assertEqual(self.db.adapt("this").getquoted(), "'this'")
        self.assertIsInstance(self.db.adapt(dict(value=10)), HstoreAdapter)

    def test_raises_execptions(self):
        "can raise all psycopg2 exceptions"
        self.assertRaises(tornpsql.ProgrammingError, self.db.query, "st nothing from th;")

    def test_json(self):
        "can providing dict as an argument will adapt to json datatype"
        self.assertDictEqual(self.db.get("select %s::json as data;", dict(data="something")).data, {u'data': u'something'})

    def test_hstore(self):
        "can parse hstore datatype as dict (kinda)"
        self.assertDictEqual(self.db.get("SELECT flags from users where flags is not null limit 1;").flags, dict(extra_feature='true'))

    def test_numeric_returns_decimal(self):
        "floats return Decimals"
        self.assertEqual(self.db.get("select balance from users where id = 1 limit 1;").balance, Decimal("7.10"))

    def test_search_path(self):
        "can set search path of query"
        self.assertEqual(self.db.get("SELECT name from users where email=%s limit 1;", 'johnnie.jast@hotmail.com').name, 'Ms. Agustin Walter')
        self.assertIs(self.db.path("schema"), self.db, "calling path did not return the db instance")
        self.assertEqual(self.db.path("schema")._change_path, "schema", "calling path did not set the temp path name")
        self.assertEqual(self.db._change_path, "schema", "calling path did not set the temp path name")
        self.assertEqual(self.db.path("other").get("SELECT name from users where id=1 limit 1;").name, "Mr. John Piere", "schema did not change")
        self.assertEqual(self.db._change_path, None, "changed path did not reset after query")

    def test_execute_with_kwargs(self):
        "can query from keyword arguments"
        self.assertDictEqual(self.db.get("SELECT x from generate_series(1,10) x where x=%(id)s;", id=1), dict(x=1))
        self.assertListEqual(self.db.query("SELECT x from generate_series(1,10) x where x > %(g)s and x < %(l)s;", g=1, l=5), [{'x': 2}, {'x': 3}, {'x': 4}])

    def test_notices(self):
        "can retreive notices"
        self.db.notices # clear other notices
        self.db.query("insert into other.users (name) values ('New Customer');")
        self.assertListEqual(self.db.notices, ["New user inserted"])
