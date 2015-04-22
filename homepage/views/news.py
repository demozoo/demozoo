from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from read_only_mode import writeable_site_required
from modal_workflow import render_modal_workflow

from demoscene.shortcuts import simple_ajax_confirmation

from homepage.forms import NewsStoryForm, NewsImageForm
from homepage.models import NewsStory, NewsImage


@writeable_site_required
def add_news(request):
	if not request.user.has_perm('homepage.add_newsstory'):
		return redirect('home')

	news_story = NewsStory()

	if request.method == 'POST':
		news_form_data = request.POST

		image_form = NewsImageForm(request.POST, request.FILES, prefix='news_image')
		if image_form.is_valid() and image_form.cleaned_data['image']:
			news_image = image_form.save()

			news_form_data = news_form_data.copy()
			news_form_data.update(image=news_image.id)
			news_story.image = news_image

		form = NewsStoryForm(news_form_data, instance=news_story)
		if form.is_valid():
			form.save()
			messages.success(request, "News story added")
			return redirect('home')
	else:
		form = NewsStoryForm(instance=news_story)

	return render(request, 'homepage/news/add_news.html', {
		'form': form,
		'image_form': NewsImageForm(prefix='news_image')
	})


@writeable_site_required
def edit_news(request, news_story_id):
	if not request.user.has_perm('homepage.change_newsstory'):
		return redirect('home')

	news_story = get_object_or_404(NewsStory, id=news_story_id)
	if request.method == 'POST':

		news_form_data = request.POST

		image_form = NewsImageForm(request.POST, request.FILES, prefix='news_image')
		if image_form.is_valid() and image_form.cleaned_data['image']:
			news_image = image_form.save()

			news_form_data = news_form_data.copy()
			news_form_data.update(image=news_image.id)
			news_story.image = news_image

		form = NewsStoryForm(news_form_data, instance=news_story)
		if form.is_valid():
			form.save()
			messages.success(request, "News story updated")
			return redirect('home')
	else:
		form = NewsStoryForm(instance=news_story)

	return render(request, 'homepage/news/edit_news.html', {
		'news_story': news_story,
		'form': form,
		'image_form': NewsImageForm(prefix='news_image')
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


def browse_images(request):
	if not request.user.has_perm('homepage.change_newsstory'):
		return redirect('home')
	images = NewsImage.objects.order_by('-created_at')

	return render_modal_workflow(
		request,
		'homepage/news/browse_images.html', 'homepage/news/browse_images.js',
		{
			'images': images,
		}
	)
