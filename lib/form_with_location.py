from __future__ import absolute_import, unicode_literals

import json
import urllib

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError


def find_locality(query):
    req = urllib.request.Request(
        "%s?%s" % (settings.GEOCODER_URL, urllib.parse.urlencode({'q': query.encode('utf-8')})),
        None,
        {'User-Agent': settings.HTTP_USER_AGENT}
    )
    page = urllib.request.urlopen(req)
    results = json.loads(page.read())
    page.close()

    result_id = results[0]['id']  # throws IndexError if no results

    req = urllib.request.Request(
        "%s%d/" % (settings.GEOCODER_URL, result_id),
        None,
        {'User-Agent': settings.HTTP_USER_AGENT}
    )
    page = urllib.request.urlopen(req)
    result = json.loads(page.read())
    page.close()

    return result


class ModelFormWithLocation(forms.ModelForm):
    def clean_location(self):
        if self.cleaned_data['location']:
            if self.instance and self.instance.location == self.cleaned_data['location']:
                self.location_has_changed = False
            else:
                self.location_has_changed = True
                # look up new location
                try:
                    self.geocoded_location = find_locality(self.cleaned_data['location'])
                except IndexError:
                    raise ValidationError('Location not recognised')

        return self.cleaned_data['location']

    def save(self, commit=True, **kwargs):
        model = super().save(commit=False, **kwargs)

        if self.cleaned_data['location']:
            if self.location_has_changed:
                model.location = self.geocoded_location['full_name']
                model.country_code = self.geocoded_location['country_code'] or ''
                model.latitude = self.geocoded_location['latitude']
                model.longitude = self.geocoded_location['longitude']
                model.geonames_id = self.geocoded_location['id']
        else:
            # clear location data
            model.country_code = ''
            model.latitude = None
            model.longitude = None
            model.geonames_id = None

        if commit:
            model.save()

        return model
