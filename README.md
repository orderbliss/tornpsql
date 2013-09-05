tornpsql
======

[![Build Status](https://secure.travis-ci.org/stevepeak/tornpsql.png)](http://travis-ci.org/stevepeak/tornpsql)

`pip install tornpsql`

`tornpsql` is a simple wrapper around PostgreSQL.
Forked from [bdarnell/torndb](https://github.com/bdarnell/torndb) which was build to support MySQL


## Usage

### Connection Methods

```python
# Method 1
import tornpsql
con = tornpsql.Connection("postgres://postgres-user:postgres-password@127.0.0.1:5432/postgres-db")
results = con.query("select column from mytable")
# Method 2
import tornpsql
con = tornpsql.Connection("127.0.0.1", "database", "postgres", "postgres-user", 5432)
results = con.query("select column from mytable")
```

### Query Methods

```python
# Get one or more results
results = con.query("select column from mytable;")
# results like [{"col": "data"}]
# Get one result
result = con.get("select column from mytable limit 1;")
# results like {"col": "data"}
```

### Close

```python
con.close()
del con
```

## Future
- Better integration with [Tornado Web](https://github.com/facebook/tornado)
  - Asynchronous handlers
