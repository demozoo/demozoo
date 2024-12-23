from django.http import JsonResponse
from django.template.loader import render_to_string


def render_modal_workflow(request, html_template, template_vars=None, json_data=None):
    """
    Render a response consisting of an HTML chunk and a JS onload chunk
    in the format required by the modal-workflow framework.
    """
    response_data = {}

    if html_template:
        response_data["html"] = render_to_string(html_template, template_vars or {}, request=request)

    if json_data:
        response_data.update(json_data)

    return JsonResponse(response_data)
