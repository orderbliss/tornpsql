import unittest
import tornpsql
import os


class tornpsqlTests(unittest.TestCase):
    def testOne(self):
        user = os.getenv("TORNPSQL_USERNAME")
        password = os.getenv("TORNPSQL_PASSWORD")
        host = os.getenv("TORNPSQL_HOST")
        database = os.getenv("TORNPSQL_DATABASE")
        db = tornpsql.Connection(host, database, user, password)
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
        db.executemany("insert into tornpsql_test (id, name) values (%s, %s) returning id",
                       (5, 'Joe'),
                       [6, "Eric"],
                       (7, "Shawn"))

        # select
        select1 = db.query("select * from tornpsql_test where id=%s;", 1)
        self.assertListEqual(select1, [{'id': 1, 'name': 'Steve'}])
        select2 = db.query("select distinct name from tornpsql_test;")
        self.assertListEqual(select2, [{'name': 'Shawn'}, {'name': 'Eric'}, {'name': 'Joe'}, {'name': 'Steve'}])

        # mogrify
        mog = db.mogrify("UPDATE some_table set column1=%s, column2=%s where col3=%s and col4=%s;",
                         'data1', 'data2', 'data3', 'data4')
        self.assertEquals(mog, "UPDATE some_table set column1='data1', column2='data2' where col3='data3' and col4='data4';")

        # drop the database
        droptable = db.execute("DROP TABLE tornpsql_test;")
        self.assertEquals(droptable, None)

        # close
        db.close()
        self.assertEquals(db._db, None)

    def testTwo(self):
        user = os.getenv("TORNPSQL_USERNAME")
        password = os.getenv("TORNPSQL_PASSWORD")
        host = os.getenv("TORNPSQL_HOST")
        database = os.getenv("TORNPSQL_DATABASE")
        url = "postgres://%s:%s@%s:5432/%s" % (user, password, host, database)
        # connect via url method
        db = tornpsql.Connection(url)
        self.assertEquals(db._db.closed, 0)
        del db

def main():
    unittest.main()

if __name__ == '__main__':
    main()
