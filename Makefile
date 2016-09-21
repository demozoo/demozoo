test:
	./manage.py test --settings=settings.test

coverage:
	coverage run ./manage.py test --settings=settings.test && coverage html
