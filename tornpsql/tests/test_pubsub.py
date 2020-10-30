import time
import unittest
import threading

import tornpsql


class PubSubThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        db = tornpsql.Connection(database='tornpsql')
        pubsub = db.pubsub()
        pubsub.subscribe(('example', 'other', 'exit', 'unsub', 'unsuball'))
        for notify in pubsub.listen():
            if notify.channel == 'exit':
                db.close()
                break
            elif notify.channel == 'unsub':
                pubsub.unsubscribe(('example', ))
            elif notify.channel == 'unsuball':
                pubsub.unsubscribe()
            else:
                db.query("insert into notices (channel, payload) values (%s, %s);", notify.channel, notify.payload)


class tornpsqlTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        PubSubThread()
        self.db = tornpsql.Connection(database="tornpsql")

    @classmethod
    def tearDownClass(self):
        self.db.execute("select pg_notify('exit', null);")

    def setUp(self):
        self.db.execute("truncate notices restart identity;")

    def test_pubsub(self):
        "can listen via pubsub"
        self.db.execute("select pg_notify('example', 'Hello world!');")
        time.sleep(.1)
        self.assertListEqual(self.db.query("SELECT * from notices"), [{"id": 1, "channel": "example", "payload": "Hello world!"}])

        self.db.execute("select pg_notify('other', 'Hello other world...?');")
        time.sleep(.1)
        results = self.db.query("SELECT * from notices")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], {"id": 1, "channel": "example", "payload": "Hello world!"})
        self.assertEqual(results[1], {"id": 2, "channel": "other", "payload": "Hello other world...?"})

        self.db.execute("select pg_notify('notlistening', 'Hello other world...?');")
        time.sleep(.1)
        results = self.db.query("SELECT * from notices")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], {"id": 1, "channel": "example", "payload": "Hello world!"})
        self.assertEqual(results[1], {"id": 2, "channel": "other", "payload": "Hello other world...?"})

    def test_unsubscribe(self):
        "can unsubscribe to channels"
        self.db.execute("select pg_notify('unsub', null);")
        time.sleep(.1)
        self.db.execute("select pg_notify('example', 'Hello world!');")
        time.sleep(.1)
        self.assertEqual(len(self.db.query("SELECT * from notices")), 0)

    def test_unsubscribe_all(self):
        "can unsubscribe to channels"
        self.db.execute("select pg_notify('unsuball', null);")
        time.sleep(.1)
        self.db.execute("select pg_notify('example', 'Hello world!');")
        time.sleep(.1)
        self.assertEqual(len(self.db.query("SELECT * from notices")), 0)
