import time
import unittest
import threading

import tornpsql


class PubSubThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.db = tornpsql.Connection()
        self.pubsub = self.db.pubsub()
        self.go = True

    def run(self):
        self.pubsub.subscribe(("example", "other"))
        while self.go:
            for notify in self.pubsub.listen():
                self.db.query("insert into notices (channel, payload) values (%s, %s);", notify.channel, notify.payload)
                if notify.channel == 'other':
                    self.go = False
                    del self.db


class tornpsqlTests(unittest.TestCase):
    def test_pubsub(self):
        "can listen via pubsub"
        db = tornpsql.Connection()
        pubsub = PubSubThread()
        pubsub.start()
        time.sleep(.1)
        
        db.execute("select pg_notify('example', 'Hello world!');")
        time.sleep(.1)
        self.assertListEqual(db.query("SELECT * from notices"), [{"id": 1, "channel": "example", "payload": "Hello world!"}])
        
        db.execute("select pg_notify('other', 'Hello other world...?');")
        time.sleep(.1)
        self.assertItemsEqual(db.query("SELECT * from notices"), [{"id": 1, "channel": "example", "payload": "Hello world!"},
                                                                  {"id": 2, "channel": "other", "payload": "Hello other world...?"}])

        db.execute("select pg_notify('notlistening', 'Hello other world...?');")
        time.sleep(.1)
        self.assertItemsEqual(db.query("SELECT * from notices"), [{"id": 1, "channel": "example", "payload": "Hello world!"},
                                                                  {"id": 2, "channel": "other", "payload": "Hello other world...?"}])
