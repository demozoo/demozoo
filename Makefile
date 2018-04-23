test:
	./manage.py test --settings=demozoo.settings.test

coverage:
	coverage run ./manage.py test --settings=demozoo.settings.test && coverage html
