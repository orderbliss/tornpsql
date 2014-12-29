open:
	subl --project ./tornpsql.sublime-project

deploy: tag upload

tag:
	git tag -m "" -a v$(shell grep "version = '" ./tornpsql/__init__.py | cut -d"'" -f 2)
	git push origin v$(shell grep "version = '" ./tornpsql/__init__.py | cut -d"'" -f 2)

upload: tag
	python setup.py sdist upload

test:
	@dropdb --if-exists tornpsql
	@createdb tornpsql
	@psql tornpsql -c 'create extension hstore;'
	@psql -f tests/test.sql tornpsql
	. venv/bin/activate; nosetests -v --with-coverage --cover-package=tornpsql --cover-html --cover-html-dir=coverage_html_report

venv:
	virtualenv venv
	. venv/bin/activate; pip install -r requirements.txt
	. venv/bin/activate; python setup.py install
	@echo "export DATABASE_URL=\"postgres://$(DATABASE_LOGIN)@127.0.0.1:5432/tornpsql\"" >> venv/bin/activate

db:
	psql tornpsql
