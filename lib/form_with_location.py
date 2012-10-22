from django import forms
from django.core.exceptions import ValidationError
from geocode import geocode

class ModelFormWithLocation(forms.ModelForm):
	def clean_location(self):
		if self.cleaned_data['location']:
			if self.instance and self.instance.location == self.cleaned_data['location']:
				self.location_has_changed = False
			else:
				self.location_has_changed = True
				# look up new location
				self.geocoded_location = geocode(self.cleaned_data['location'])
				if not self.geocoded_location:
					raise ValidationError('Location not recognised')
					
		return self.cleaned_data['location']
	
	def save(self, commit = True, **kwargs):
		model = super(ModelFormWithLocation, self).save(commit = False, **kwargs)
		
		if self.cleaned_data['location']:
			if self.location_has_changed:
				model.location = self.geocoded_location['location']
				model.country_code = self.geocoded_location['country_code'] or ''
				model.latitude = self.geocoded_location['latitude']
				model.longitude = self.geocoded_location['longitude']
				model.woe_id = self.geocoded_location['woeid']
		else:
			# clear location data
			model.country_code = ''
			model.latitude = None
			model.longitude = None
			model.woe_id = None
		
		if commit:
			model.save()
			
		return model
