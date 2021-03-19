test:
	./manage.py test --settings=demozoo.settings.test

coverage:
	coverage run ./manage.py test --settings=demozoo.settings.test \
	&& DEMOZOO_SUBSITE=zxdemo coverage run -a ./manage.py test zxdemo --settings=demozoo.settings.test \
	&& coverage run -a ./manage.py test productions.tests.test_readonly --settings=demozoo.settings.test_readonly \
	&& coverage html

lint:
	isort --check-only --diff .
