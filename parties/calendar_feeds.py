# This file provides feed data to the calendar feed endpoints, and caches the results
# in redis

import redis
from django.conf import settings
from django.urls import reverse
from datetime import date, timedelta
import icalendar
from parties.models import Party

CACHE_PREFIX='calendar_feeds/'
MAX_AGE=(24*60*60) # how long in seconds is a cache entry valid for?

feed_metadata = {
    'main': {'summary':'A feed of all upcoming demo parties, and demo parties from the past year.'},
    'historical': {'summary':'A feed of all demo parties known to Demozoo, past and present.'},
    'online_only': {'summary':'Upcoming online-only demo parties.'},
}

def full_path(fpath):
    return f'{CACHE_PREFIX}{fpath}'

def cache_get(fpath):
    # Fetches a previously cached feed from redis, or returns None
    r = redis.StrictRedis.from_url(settings.REDIS_URL)
    p = full_path(fpath)
    return r.get(p)

def cache_set(fpath, data):
    # Stores a calendar feed in redis, with an expiry time
    r = redis.StrictRedis.from_url(settings.REDIS_URL)
    p = full_path(fpath)
    r.set(p, data, ex=MAX_AGE)

def query_parties(fpath):
    # Fetches the data for the specified feed
    min_time = date.today() - timedelta(days=365) # approximate the time one year ago
    if fpath=='main':
        return Party.objects.filter(start_date_date__gte=min_time).order_by("start_date_date", "end_date_date", "name")
    if fpath == 'historical':
        return Party.objects.order_by("start_date_date", "end_date_date", "name")
    if fpath == 'online_only':
        return Party.objects.filter(start_date_date__gte=min_time, is_online=True).order_by("start_date_date", "end_date_date", "name")

    parts = fpath.split('/')
    if parts[0] == 'country':
        code = parts[1]
        return Party.objects.filter(start_date_date__gte=min_time, country_code=code).order_by("start_date_date", "end_date_date", "name")

def build_feed(fpath, url_base):
    # Generates the ical file. Only called on a cache miss
    cal = icalendar.Calendar()
    meta = feed_metadata.get(fpath)
    if meta is None:
        cal['summary'] = 'An automatically generated calendar feed from Demozoo'
    else:
        cal['summary'] = meta['summary']
    for party in query_parties(fpath):
        if party.start_date_precision in ['d']:
            ev = icalendar.Event()
            ev['uid'] = f'DEMOZOO_{fpath}_PARTY_{party.id}'
            ev['dtstart'] = party.start_date.date
            ev['dtend'] = party.end_date.date
            ev['summary'] = party.name
            if url_base.endswith('/'):
                url_base = url_base[0:-1]
            demozoo_url = url_base + reverse('party', kwargs={'party_id':party.id})
            desc = f'{demozoo_url}\n'
            ev['description'] = desc
            if party.location:
                ev['location'] = party.location
            cal.add_component(ev)
    data = cal.to_ical()
    return data
    
def get_feed(fpath, url_base):
    # Look for this feed in the cache
    cached = cache_get(fpath)
    if cached is not None:
        return cached
    # Need to rebuild this feed
    data = build_feed(fpath, url_base)
    cache_set(fpath, data)
    return data
