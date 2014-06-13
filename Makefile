open:
	subl --project ./tornpsql.sublime-project

deploy: tag upload

tag:
	git tag -m "" -a v$(shell grep "version = '" ./tornpsql/__init__.py | cut -d"'" -f 2)
	git push origin v$(shell grep "version = '" ./tornpsql/__init__.py | cut -d"'" -f 2)

upload:
	python setup.py sdist upload

test:
	@psql tornpsql -f tests/test.sql
	. venv/bin/activate; nosetests -v --with-coverage --cover-package=tornpsql --cover-html --cover-html-dir=coverage_html_report

venv:
	virtualenv venv
	. venv/bin/activate; pip install -r requirements.txt
	. venv/bin/activate; python setup.py install
