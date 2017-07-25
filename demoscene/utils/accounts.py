def is_ip_banned(request):
	return (request.META['REMOTE_ADDR'] in ['81.234.236.23', '81.230.148.230'])
