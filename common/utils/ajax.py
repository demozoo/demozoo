def request_is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'
