from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from read_only_mode import writeable_site_required
import datetime

from forums.models import Topic, Post
from forums.forms import NewTopicForm

def index(request):
	topics = Topic.objects.order_by('-last_post_at')

	return render(request, 'forums/index.html', {
		'topics': topics,
	})

@writeable_site_required
@login_required
def new_topic(request):
	if request.POST:
		form = NewTopicForm(request.POST)
		if form.is_valid():
			topic = Topic.objects.create(title=form.cleaned_data['title'], last_post_at=datetime.datetime.now())
			Post.objects.create(user=request.user, topic=topic, body=form.cleaned_data['body'])
			return redirect(topic.get_absolute_url())
	else:
		form = NewTopicForm()

	return render(request, 'forums/new_topic.html', {
		'form': form,
	})

def topic(request, topic_id):
	topic = get_object_or_404(Topic, id=topic_id)
	posts = topic.posts.order_by('created_at')

	return render(request, 'forums/topic.html', {
		'topic': topic,
		'posts': posts
	})
