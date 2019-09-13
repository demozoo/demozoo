import json
import urllib
import urllib2

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError


def find_locality(query):
    req = urllib2.Request(
        "%s?%s" % (settings.GEOCODER_URL, urllib.urlencode({'q': query.encode('utf-8')})),
        None,
        {'User-Agent': settings.HTTP_USER_AGENT}
    )
    page = urllib2.urlopen(req)
    results = json.loads(page.read())
    page.close()

    result_id = results[0]['id']  # throws IndexError if no results

    req = urllib2.Request(
        "%s%d/" % (settings.GEOCODER_URL, result_id),
        None,
        {'User-Agent': settings.HTTP_USER_AGENT}
    )
    page = urllib2.urlopen(req)
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
        model = super(ModelFormWithLocation, self).save(commit=False, **kwargs)

        if self.cleaned_data['location']:
            if self.location_has_changed:
                model.location = self.geocoded_location['full_name']
                model.country_code = self.geocoded_location['country_code'] or ''
                model.latitude = self.geocoded_location['latitude']
                model.longitude = self.geocoded_location['longitude']
                model.geonames_id = self.geocoded_location['id']
                model.woe_id = None
        else:
            # clear location data
            model.country_code = ''
            model.latitude = None
            model.longitude = None
            model.geonames_id = None
            model.woe_id = None

        if commit:
            model.save()

        return model
