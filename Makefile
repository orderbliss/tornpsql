open:
	subl --project ./tornpsql.sublime-project

deploy: tag upload

tag:
	git tag -m "" -a v$(shell grep "version = '" ./tornpsql/__init__.py | cut -d"'" -f 2)
	git push origin v$(shell grep "version = '" ./tornpsql/__init__.py | cut -d"'" -f 2)

upload:
	python setup.py sdist upload

test:
	. venv/bin/activate; pip uninstall -y tornpsql
	. venv/bin/activate; python setup.py install
	. venv/bin/activate; python -m unittest discover -s tests

venv:
	virtualenv venv
	. venv/bin/activate; pip install -r requirements.txt
	. venv/bin/activate; python setup.py install
