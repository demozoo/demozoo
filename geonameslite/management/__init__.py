from django.db.models.signals import post_syncdb

import geonameslite.models

def my_callback(sender, **kwargs):
	from django.db import connections
	cursor = connections['geonameslite'].cursor()

	if geonameslite.models.Country in kwargs['created_models']:
		cursor.execute("CREATE INDEX geonameslite_country_name_idx ON geonameslite_country (UPPER(name))")
		cursor.execute("CREATE INDEX geonameslite_country_name_like_idx ON geonameslite_country (UPPER(name) varchar_pattern_ops)")

	if geonameslite.models.Admin1Code in kwargs['created_models']:
		cursor.execute("CREATE INDEX geonameslite_admin1code_name_idx ON geonameslite_admin1code (UPPER(name))")
		cursor.execute("CREATE INDEX geonameslite_admin1code_name_like_idx ON geonameslite_admin1code (UPPER(name) varchar_pattern_ops)")

	if geonameslite.models.Admin2Code in kwargs['created_models']:
		cursor.execute("CREATE INDEX geonameslite_admin2code_name_idx ON geonameslite_admin2code (UPPER(name))")
		cursor.execute("CREATE INDEX geonameslite_admin2code_name_like_idx ON geonameslite_admin2code (UPPER(name) varchar_pattern_ops)")

	if geonameslite.models.Locality in kwargs['created_models']:
		cursor.execute("CREATE INDEX geonameslite_locality_name_idx ON geonameslite_locality (UPPER(name))")
		cursor.execute("CREATE INDEX geonameslite_locality_name_like_idx ON geonameslite_locality (UPPER(name) varchar_pattern_ops)")

	if geonameslite.models.AlternateName in kwargs['created_models']:
		cursor.execute("CREATE INDEX geonameslite_alternatename_name_idx ON geonameslite_alternatename (UPPER(name))")
		cursor.execute("CREATE INDEX geonameslite_alternatename_name_like_idx ON geonameslite_alternatename (UPPER(name) varchar_pattern_ops)")

post_syncdb.connect(my_callback, sender=geonameslite.models)
