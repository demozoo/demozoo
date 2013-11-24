class GeonamesLiteRouter(object):
	"""A router to direct all tables to the geonameslite db"""
	def db_for_read(self, model, **hints):
		if model._meta.app_label == 'geonameslite':
			return 'geonameslite'
		return None

	def db_for_write(self, model, **hints):
		if model._meta.app_label == 'geonameslite':
			return 'geonameslite'
		return None

	def allow_relation(self, obj1, obj2, **hints):
		if obj1._meta.app_label == 'geonameslite' and obj2._meta.app_label == 'geonameslite':
			return True
		return None

	def allow_syncdb(self, db, model):
		if db == 'geonameslite':
			return model._meta.app_label == 'geonameslite'
		elif model._meta.app_label == 'geonameslite':
			return False
		return None
