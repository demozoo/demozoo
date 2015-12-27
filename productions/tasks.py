from celery.task import task
import datetime

from productions.models import ProductionLink


@task(rate_limit='12/m', ignore_result=True)
def fetch_production_link_embed_data(productionlink_id):
	try:
		production_link = ProductionLink.objects.get(id=productionlink_id)
	except ProductionLink.DoesNotExist:
		# guess it was deleted in the meantime, then.
		return

	last_month = datetime.date.today() - datetime.timedelta(days=30)
	if production_link.embed_data_last_fetch_time and production_link.embed_data_last_fetch_time > last_month:
		return
	if production_link.embed_data_last_error_time and production_link.embed_data_last_error_time > last_month:
		return

	try:
		production_link.fetch_embed_data()
	except:
		production_link.embed_data_last_error_time = datetime.datetime.now()
		production_link.save()
