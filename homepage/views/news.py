from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from read_only_mode import writeable_site_required

from demoscene.shortcuts import simple_ajax_confirmation

from homepage.forms import NewsStoryForm
from homepage.models import NewsStory

@writeable_site_required
def add_news(request):
	if not request.user.has_perm('homepage.add_newsstory'):
		return redirect('home')

	if request.method == 'POST':
		form = NewsStoryForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, "News story added")
			return redirect('home')
	else:
		form = NewsStoryForm()

	return render(request, 'homepage/add_news.html', {
		'form': form,
	})


@writeable_site_required
def edit_news(request, news_story_id):
	if not request.user.has_perm('homepage.change_newsstory'):
		return redirect('home')

	news_story = get_object_or_404(NewsStory, id=news_story_id)
	if request.method == 'POST':
		form = NewsStoryForm(request.POST, instance=news_story)
		if form.is_valid():
			form.save()
			messages.success(request, "News story updated")
			return redirect('home')
	else:
		form = NewsStoryForm(instance=news_story)

	return render(request, 'homepage/edit_news.html', {
		'news_story': news_story,
		'form': form,
	})


@writeable_site_required
def delete_news(request, news_story_id):
	if not request.user.has_perm('homepage.delete_newsstory'):
		return redirect('home')

	news_story = get_object_or_404(NewsStory, id=news_story_id)

	if request.method == 'POST':
		if request.POST.get('yes'):
			news_story.delete()
			messages.success(request, "News story deleted")
			return redirect('home')
		else:
			return redirect('edit_news', news_story_id)
	else:
		return simple_ajax_confirmation(request,
			reverse('delete_news', args=[news_story_id]),
			"Are you sure you want to delete this news story?",
			html_title="Deleting news story: %s" % news_story.title)
