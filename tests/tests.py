import unittest
import tornpsql
import os
from decimal import Decimal


class tornpsqlTests(unittest.TestCase):
    def test_one(self):
        user = os.getenv("TORNPSQL_USERNAME")
        host = os.getenv("TORNPSQL_HOST")
        database = os.getenv("TORNPSQL_DATABASE")
        db = tornpsql.Connection(host, database, user)
        # assert database connection
        self.assertEquals(db._db.closed, 0)
        db.execute("DROP TABLE IF EXISTS tornpsql_test;")
        createtable = db.execute("CREATE TABLE tornpsql_test (id int, name varchar);")
        self.assertEquals(createtable, None)

        # single insert
        insert1 = db.execute("INSERT INTO tornpsql_test values (%s, %s) returning id;", 1, 'Steve')
        self.assertListEqual(insert1, [{'id': 1}])
        insert2 = db.execute("INSERT INTO tornpsql_test values (%s, %s) returning id, name;", 2, 'Steve')
        self.assertListEqual(insert2, [{'id': 2, 'name': 'Steve'}])
        insert3 = db.get("INSERT INTO tornpsql_test values (%s, %s) returning id;", 3, 'Steve')
        self.assertDictEqual(insert3, {'id': 3})
        insert4 = db.query("INSERT INTO tornpsql_test values (%s, %s) returning id;", 4, 'Steve')
        self.assertListEqual(insert4, [{'id': 4}])
        db.executemany("INSERT INTO tornpsql_test (id, name) values (%s, %s) returning id",
                       (5, 'Joe'), [6, "Eric"], (7, "Shawn"))

        # select
        select1 = db.query("SELECT * from tornpsql_test where id=%s;", 1)
        self.assertListEqual(select1, [{'id': 1, 'name': 'Steve'}])
        select2 = db.query("SELECT distinct name from tornpsql_test;")
        self.assertListEqual(select2, [{'name': 'Shawn'}, {'name': 'Eric'}, {'name': 'Joe'}, {'name': 'Steve'}])

        # drop the database
        droptable = db.execute("DROP TABLE tornpsql_test;")
        self.assertEquals(droptable, None)

        # close
        db.close()
        self.assertEquals(db._db, None)

    def test_two(self):
        user = os.getenv("TORNPSQL_USERNAME")
        host = os.getenv("TORNPSQL_HOST")
        database = os.getenv("TORNPSQL_DATABASE")
        url = "postgres://%s:@%s:5432/%s" % (user, host, database)
        # connect via url method
        db = tornpsql.Connection(url)
        self.assertEquals(db._db.closed, 0)
        del db

    def test_three(self):
        db = tornpsql.Connection(os.getenv("TORNPSQL_HOST"), os.getenv("TORNPSQL_DATABASE"), os.getenv("TORNPSQL_USERNAME"))
        db.execute("DROP EXTENSION if exists hstore cascade;")
        db.execute("CREATE EXTENSION hstore;")
        db.execute("DROP TABLE if exists hstore_test;")
        db.execute("CREATE TABLE hstore_test (demo hstore);")
        # need to reconnect to utilize the hstore
        db = tornpsql.Connection(os.getenv("TORNPSQL_HOST"), os.getenv("TORNPSQL_DATABASE"), os.getenv("TORNPSQL_USERNAME"))
        d = dict(value1="1", value2="2", value3="eric da man")
        self.assertEqual(db.hstore(d), '"value3"=>"eric da man","value2"=>"2","value1"=>"1"')
        db.execute("INSERT INTO hstore_test (demo) values (%s);", db.hstore(d))
        self.assertDictEqual(db.get("SELECT demo from hstore_test limit 1;").demo, d)

    def test_four(self):
        db = tornpsql.Connection(os.getenv("TORNPSQL_HOST"), os.getenv("TORNPSQL_DATABASE"), os.getenv("TORNPSQL_USERNAME"))
        db.execute("DROP TABLE if exists test_money;")
        db.execute("CREATE TABLE if not exists test_money (x money);")
        db.execute("INSERT INTO test_money values (5.99::money);")
        money = db.get("SELECT x from test_money limit 1;").x
        self.assertEqual(money, Decimal("5.99"))
        self.assertTrue(isinstance(money, Decimal))

    def test_kwarg_set(self):
        db = tornpsql.Connection(os.getenv("TORNPSQL_HOST"), os.getenv("TORNPSQL_DATABASE"), os.getenv("TORNPSQL_USERNAME"))
        db.execute("DROP TABLE if exists example_update;")
        db.execute("CREATE TABLE example_update (a int, b text, c int);")
        db.query("INSERT INTO example_update values (1, 'Hello', 2);")
        db.query("INSERT INTO example_update values (3, 'Hello', 4);")
        db.query("UPDATE example_update SET __data__ where a=%s;", 1, b="this is cool!", c=10)
        data = db.query("SELECT * from example_update order by a asc;")
        self.assertListEqual(data, [{'a': 1, 'b': 'this is cool!', 'c': 10}, {'a': 3, 'b': 'Hello', 'c': 4}])

    def test_search_path(self):
        db = tornpsql.Connection(os.getenv("TORNPSQL_HOST"), os.getenv("TORNPSQL_DATABASE"), os.getenv("TORNPSQL_USERNAME"),
                                 search_path="public")
        db.execute("DROP TABLE if exists example_sp;")
        db.query("CREATE TABLE example_sp (a int);")
        db.query("INSERT INTO example_sp (a) values (1), (2);")
        db.execute("DROP SCHEMA if exists other_schema cascade;")
        db.execute("CREATE SCHEMA other_schema;")
        db.path('other_schema').execute("DROP TABLE if exists example_sp;")
        db.path('other_schema').query("CREATE TABLE example_sp (a int);")
        db.path('other_schema').query("INSERT INTO example_sp (a) values (3), (4);")
        self.assertListEqual(db.query("SELECT a from example_sp;"), [{'a':1}, {'a':2}])
        self.assertListEqual(db.path('other_schema').query("SELECT a from example_sp;"), [{'a':3}, {'a':4}])
        

if __name__ == '__main__':
    unittest.main()
