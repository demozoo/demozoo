from django.shortcuts import render, redirect

from homepage.models import Banner


def index(request):
	if not request.user.has_perm('homepage.add_banner'):
		return redirect('home')

	banners = Banner.objects.select_related('banner_image').order_by('-created_at')

	return render(request, 'homepage/banners/index.html', {
		'banners': banners,
	})
