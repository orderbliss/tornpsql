Tornpsql [![Build Status](https://secure.travis-ci.org/stevepeak/tornpsql.png)](http://travis-ci.org/stevepeak/tornpsql) [![Version](https://pypip.in/v/tornpsql/badge.png)](https://github.com/stevepeak/tornpsql) [![Coverage Status](https://coveralls.io/repos/stevepeak/tornpsql/badge.png)](https://coveralls.io/r/stevepeak/tornpsql)
======

`pip install tornpsql`

> Forked/ported from [bdarnell/torndb](https://github.com/bdarnell/torndb) which is build to support MySQL

## Features
- Query via `args` or `kwargs`
- [set search_path](#set-search_path)
- [Query from Files](#query-files)
  - including references
- [Pubsub](#pubsub)

## Usage
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

## Set search_path
Set the `search_path` for the duration of the proceeding query.

```python
# set the "default" search_path to public
db = tornpsql.Connection(search_path="public")
results = db.path("another_schema").query("select column from mytable")
results = db.path("another_schema,and_another").query("select column from mytable")
# this will use search path: "public"
results = db.query("select column from mytable")
```

## Query Files

```sql
-- main.sql
create table example (id serial primary key);
\ir other.sql
```

```sql
-- other.sql
insert into example values (1, 2, 3);
```

```python
db = tornpsql.Connection()
db.file("main.sql")
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
