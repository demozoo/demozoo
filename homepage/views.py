from django.shortcuts import render

from homepage.models import Banner, Teaser, NewsStory
from forums.models import Topic

def home(request):
	if request.user.is_authenticated():
		banners = Banner.objects.filter(show_for_logged_in_users=True).order_by('-created_at')[:1]
		teasers = Teaser.objects.filter(show_for_logged_in_users=True).order_by('-created_at')[:3]
	else:
		banners = Banner.objects.filter(show_for_anonymous_users=True).order_by('-created_at')[:1]
		teasers = Teaser.objects.filter(show_for_anonymous_users=True).order_by('-created_at')[:3]

	try:
		banner = banners[0]
	except IndexError:
		banner = None

	return render(request, 'home.html', {
		'banner': banner,
		'teasers': teasers,
		'news_stories': NewsStory.objects.order_by('-created_at')[:6],
		'forum_topics': Topic.objects.order_by('-last_post_at').select_related('created_by_user', 'last_post_by_user')[:5],
	})


def not_the_homepage(request):
	return render(request, 'home.html', {
		'banner': None,
		'teasers': Teaser.objects.none(),
		'news_stories': NewsStory.objects.none(),
		'forum_topics': Topic.objects.order_by('-last_post_at').select_related('created_by_user', 'last_post_by_user')[:5],
	})
