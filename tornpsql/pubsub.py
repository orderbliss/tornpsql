from select import select
import psycopg2.extensions


class PubSub(object):
    def __init__(self, db):
        self._db = db
        db.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        self._cur = db.cursor()
        self._channels = []

    def subscribe(self, channels):
        assert type(channels) in (tuple, list), "Invalid channels. Must be tuple or list of strings"
        self._channels = list(channels)

    def unsubscribe(self, channel=None):
        if channel:
            assert channel in self._channels, "Channel not listened to."
            self._cur.execute("UNLISTEN %s;" % channel)
            self._channels.remove(channel)
        else:
            for channel in self._channels:
                self._cur.execute("UNLISTEN %s;" % channel)
            self._channels = []

    def __iter__(self):
        while len(self._channels) > 0:
            if select([self._db], [], [], 5) != ([], [], []):
                self._db.poll()
                while self._db.notifies:
                    yield self._db.notifies.pop()

    def listen(self):
        assert self._channels, "No channels to listen to."
        for channel in self._channels:
            self._cur.execute("LISTEN %s;" % channel)
        return self
