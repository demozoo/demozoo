from django.conf.urls import patterns

urlpatterns = patterns('homepage.views',
	(r'^$', 'home.home', {}, 'home'),

	(r'^news/new/$', 'news.add_news', {}, 'add_news'),
	(r'^news/(\d+)/edit/$', 'news.edit_news', {}, 'edit_news'),
	(r'^news/(\d+)/delete/$', 'news.delete_news', {}, 'delete_news'),
	(r'^news/browse_images/$', 'news.browse_images', {}, 'news_images_browse'),
)
