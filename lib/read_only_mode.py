from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import render


if settings.SITE_IS_WRITEABLE:
	# don't do any decorating, just return the view function unchanged
	def writeable_site_required(view_func):
		return view_func
else:
	def writeable_site_required(view_func):
		def replacement_view_func(request, *args, **kwargs):
			if request.is_ajax():
				# output the 'sorry' message on a template,
				# rather than doing a redirect (which screws with AJAX)
				return render(request, 'read_only_mode.html')
			else:
				messages.error(request, "Sorry, the website is in read-only mode at the moment. We'll get things back to normal as soon as possible.")
				return HttpResponseRedirect('/')

		return replacement_view_func
