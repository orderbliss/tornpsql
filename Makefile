open:
	subl --project ./tornpsql.sublime-project

deploy: tag upload

tag:
	git tag -m "" -a v$(shell grep "version = '" ./tornpsql/__init__.py | cut -d"'" -f 2)
	git push origin v$(shell grep "version = '" ./tornpsql/__init__.py | cut -d"'" -f 2)

upload:
	python setup.py sdist upload

test:
	python -m unittest discover -s tests
