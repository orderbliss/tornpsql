import unittest
import tornpsql
import os
import threading
import time

class PubSubThread(threading.Thread):
    def __init__(self, ut):
        threading.Thread.__init__(self)
        self.ut = ut

    def run(self):
        user = os.getenv("TORNPSQL_USERNAME")
        host = os.getenv("TORNPSQL_HOST")
        database = os.getenv("TORNPSQL_DATABASE")
        db = tornpsql.Connection(host, database, user)
        self.pubsub = db.pubsub()
        self.pubsub.subscribe(("example", "other"))
        for notify in self.pubsub.listen():
            assert notify.channel in self.pubsub._channels
            if notify.channel == 'example':
                self.ut.assertEquals('Hello World', notify.payload)
            elif notify.channel == 'other':
                break


class tornpsqlTests(unittest.TestCase):
    def test_one(self):
        p = PubSubThread(self)
        p.start()
        user = os.getenv("TORNPSQL_USERNAME")
        host = os.getenv("TORNPSQL_HOST")
        database = os.getenv("TORNPSQL_DATABASE")
        db = tornpsql.Connection(host, database, user)
        time.sleep(1)
        db.execute("select pg_notify('example', 'Hello World');")
        time.sleep(1)
        db.execute("select pg_notify('other', 'Hello World');")
        time.sleep(1)
        del p

    def test_two(self):
        p = PubSubThread(self)
        p.start()
        user = os.getenv("TORNPSQL_USERNAME")
        host = os.getenv("TORNPSQL_HOST")
        database = os.getenv("TORNPSQL_DATABASE")
        db = tornpsql.Connection(host, database, user)
        time.sleep(1)
        db.execute("select pg_notify('example', 'Hello World');")
        time.sleep(1)
        p.pubsub.unsubscribe('example')
        self.assertTrue('example' not in p.pubsub._channels)
        self.assertTrue('other' in p.pubsub._channels)
        db.execute("select pg_notify('other', 'Hello World');")
        time.sleep(1)
        del p

        
if __name__ == '__main__':
    unittest.main()
