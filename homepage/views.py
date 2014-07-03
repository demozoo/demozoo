from django.shortcuts import render

from homepage.models import Banner, NewsStory
from forums.models import Topic
from productions.models import Production

def home(request):
	if request.user.is_authenticated():
		banner = Banner.objects.filter(show_for_logged_in_users=True).order_by('-created_at').first()
	else:
		banner = Banner.objects.filter(show_for_anonymous_users=True).order_by('-created_at').first()

	latest_releases = Production.objects.filter(
		default_screenshot__isnull=False, release_date_date__isnull=False
	).select_related(
		'default_screenshot'
	).prefetch_related(
		'author_nicks', 'author_affiliation_nicks', 'platforms', 'types'
	).order_by('-release_date_date', '-created_at')[:5]

	return render(request, 'homepage/home.html', {
		'banner': banner,
		'news_stories': NewsStory.objects.order_by('-created_at')[:6],
		'forum_topics': Topic.objects.order_by('-last_post_at').select_related('created_by_user', 'last_post_by_user')[:5],
		'latest_releases': latest_releases,
	})
