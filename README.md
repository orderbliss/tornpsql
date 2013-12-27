Tornpsql [![Build Status](https://secure.travis-ci.org/stevepeak/tornpsql.png)](http://travis-ci.org/stevepeak/tornpsql) [![Version](https://pypip.in/v/tornpsql/badge.png)](https://github.com/stevepeak/tornpsql)
======

`pip install tornpsql`

> Forked/ported from [bdarnell/torndb](https://github.com/bdarnell/torndb) which is build to support MySQL


## Connect and Query

```python
# Method 1
import tornpsql
db = tornpsql.Connection("postgres://postgres-user:postgres-password@127.0.0.1:5432/postgres-db")
results = db.query("select column from mytable")
# Method 2
import tornpsql
db = tornpsql.Connection("127.0.0.1", "database", "postgres", "postgres-user", 5432)
results = db.query("select column from mytable")
```

## PubSub
```python
db = tornpsql.Connection()
pubsub = db.pubsub()
pubsub.subscribe( ("channel_1", ) )
for notify in pubsub.listen():
    print notify.pid, notify.channel, notify.payload
```

#### Via Threading
```python
class PubSubThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.db = tornpsql.Connection()
        self.pubsub = self.db.pubsub()
        self.pubsub.subscribe( ("channel_1", "channel_2") )

    def run(self):
        for notify in self.pubsub.listen():
            print notify.pid, notify.channel, notify.payload


pubsub = PubSubThread()
```
