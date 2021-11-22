from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from modal_workflow import render_modal_workflow
from read_only_mode import writeable_site_required

from demoscene.views.generic import AjaxConfirmationView
from homepage.forms import NewsImageForm, NewsStoryForm
from homepage.models import NewsImage, NewsStory


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


class DeleteNewsStoryView(AjaxConfirmationView):
    action_url_path = 'delete_news'

    def get_object(self, request, news_story_id):
        return NewsStory.objects.get(id=news_story_id)

    def is_permitted(self):
        return self.request.user.has_perm('homepage.delete_newsstory')

    def perform_action(self):
        self.object.delete()
        messages.success(self.request, "News story deleted")

    def get_cancel_url(self):
        return reverse('edit_news', args=[self.object.id])

    def get_redirect_url(self):
        return reverse('home')

    def get_permission_denied_url(self):
        return reverse('home')

    def get_message(self):
        return "Are you sure you want to delete this news story?"

    def get_html_title(self):
        return "Deleting news story: %s" % str(self.object.title)


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
