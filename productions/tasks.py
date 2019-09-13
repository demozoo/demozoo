from celery.task import task
import datetime
import urllib2

from productions.models import ProductionLink


@task(rate_limit='12/m', ignore_result=True)
def fetch_production_link_embed_data(productionlink_id):
    try:
        production_link = ProductionLink.objects.get(id=productionlink_id)
    except ProductionLink.DoesNotExist:
        # guess it was deleted in the meantime, then.
        return

    last_month = datetime.datetime.now() - datetime.timedelta(days=30)
    if production_link.embed_data_last_fetch_time and production_link.embed_data_last_fetch_time > last_month:
        return
    if production_link.embed_data_last_error_time and production_link.embed_data_last_error_time > last_month:
        return

    try:
        production_link.fetch_embed_data()
    except:
        production_link.embed_data_last_error_time = datetime.datetime.now()
        production_link.save()


@task(rate_limit='30/m', ignore_result=True)
def clean_dead_youtube_link(productionlink_id):
    """Poll oembed endpoint for the given youtube link, and delete if it's a 404"""
    try:
        production_link = ProductionLink.objects.get(id=productionlink_id)
    except ProductionLink.DoesNotExist:
        # guess it was deleted in the meantime, then.
        return

    try:
        production_link.link.get_embed_data(oembed_only=True)
    except urllib2.HTTPError as e:
        if e.code == 404:
            print("404 on %s - deleting" % production_link.link)
            production_link.delete()
