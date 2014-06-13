import time
import unittest
import threading

import tornpsql


class PubSubThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        db = tornpsql.Connection()
        pubsub = db.pubsub()
        pubsub.subscribe(("example", "other", "exit"))
        for notify in pubsub.listen():
            db.query("insert into notices (channel, payload) values (%s, %s);", notify.channel, notify.payload)
            if notify.channel == 'exit':
                del db
                break


class tornpsqlTests(unittest.TestCase):
    def test_pubsub(self):
        "can listen via pubsub"
        PubSubThread()
        try:
            db = tornpsql.Connection()
            db.execute("truncate notices restart identity;")
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
            db.execute("select pg_notify('exit', null);")
        except:
            db.execute("select pg_notify('exit', null);")
            raise
