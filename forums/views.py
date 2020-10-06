from __future__ import absolute_import, unicode_literals

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from read_only_mode import writeable_site_required
import datetime

from forums.models import Topic, Post
from forums.forms import NewTopicForm, ReplyForm

POSTS_PER_PAGE = 50


def index(request):
    topics = Topic.objects.order_by('-last_post_at').select_related('created_by_user', 'last_post_by_user')

    return render(request, 'forums/index.html', {
        'menu_section': 'forums',
        'topics': topics,
    })


@writeable_site_required
@login_required
def new_topic(request):
    if request.POST:
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = Topic.objects.create(
                title=form.cleaned_data['title'],
                created_by_user=request.user,
                last_post_at=datetime.datetime.now(),
                last_post_by_user=request.user
            )
            Post.objects.create(user=request.user, topic=topic, body=form.cleaned_data['body'])
            return redirect(topic.get_absolute_url())
    else:
        form = NewTopicForm()

    return render(request, 'forums/new_topic.html', {
        'menu_section': 'forums',
        'form': form,
    })


def topic(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    posts = topic.posts.order_by('created_at').select_related('user')
    paginator = Paginator(posts, POSTS_PER_PAGE)

    page = request.GET.get('page')
    try:
        posts_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        # If page is not an integer, or out of range (e.g. 9999), deliver last page of results.
        posts_page = paginator.page(paginator.num_pages)

    return render(request, 'forums/topic.html', {
        'menu_section': 'forums',
        'topic': topic,
        'posts': posts_page,
        'form': ReplyForm(),
    })


def post(request, post_id):
    """ topic view but ensuring that we display the page that contains the given post """
    post = get_object_or_404(Post, id=post_id)
    topic = post.topic
    posts = topic.posts.order_by('created_at').select_related('user')

    post_offset = topic.posts.filter(created_at__lt=post.created_at).count()
    paginator = Paginator(posts, POSTS_PER_PAGE)

    page = (post_offset / POSTS_PER_PAGE) + 1
    posts_page = paginator.page(page)

    return render(request, 'forums/topic.html', {
        'menu_section': 'forums',
        'topic': topic,
        'posts': posts_page,
        'form': ReplyForm(),
    })


@writeable_site_required
@login_required
def topic_reply(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    post = Post(topic=topic, user=request.user)

    if request.POST:
        form = ReplyForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            topic.last_post_at = post.created_at
            topic.last_post_by_user = request.user
            topic.reply_count = topic.posts.count() - 1
            topic.save()
            return redirect(topic.get_absolute_url() + ('#post-%d' % post.id))
        else:
            # the only possible error is leaving the box totally empty.
            # Redirect back to topic page in that case
            return redirect(topic.get_absolute_url())
    else:
        form = ReplyForm(instance=post)

    return render(request, 'forums/add_reply.html', {
        'menu_section': 'forums',
        'topic': topic,
        'form': form,
    })
