from django.shortcuts import render

def home(request):
	return render(request, 'zxdemo/home.html', {})
