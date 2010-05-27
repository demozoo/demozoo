from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

def render(request, template, context={}):
	return render_to_response(template, context, context_instance=RequestContext(request))
