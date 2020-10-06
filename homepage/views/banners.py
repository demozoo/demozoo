from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from read_only_mode import writeable_site_required
from modal_workflow import render_modal_workflow

from demoscene.shortcuts import simple_ajax_confirmation

from homepage.forms import BannerForm, BannerImageForm
from homepage.models import Banner, BannerImage


def index(request):
    if not request.user.has_perm('homepage.add_banner'):
        return redirect('home')

    banners = Banner.objects.select_related('banner_image').order_by('-created_at')

    return render(request, 'homepage/banners/index.html', {
        'banners': banners,
    })


@writeable_site_required
def add_banner(request):
    if not request.user.has_perm('homepage.add_banner'):
        return redirect('home')

    banner = Banner()

    if request.method == 'POST':
        banner_form_data = request.POST

        image_form = BannerImageForm(request.POST, request.FILES, prefix='bannerimageform')
        if image_form.is_valid() and image_form.cleaned_data['image']:
            banner_image = image_form.save()

            banner_form_data = banner_form_data.copy()
            banner_form_data.update(banner_image=banner_image.id)
            banner.banner_image = banner_image

        form = BannerForm(banner_form_data, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, "Banner added")
            return redirect('home')
    else:
        form = BannerForm(instance=banner)

    return render(request, 'homepage/banners/add_banner.html', {
        'form': form,
        'image_form': BannerImageForm(prefix='bannerimageform')
    })


@writeable_site_required
def edit_banner(request, banner_id):
    if not request.user.has_perm('homepage.change_banner'):
        return redirect('home')

    banner = get_object_or_404(Banner, id=banner_id)
    if request.method == 'POST':

        banner_form_data = request.POST

        image_form = BannerImageForm(request.POST, request.FILES, prefix='bannerimageform')
        if image_form.is_valid() and image_form.cleaned_data['image']:
            banner_image = image_form.save()

            banner_form_data = banner_form_data.copy()
            banner_form_data.update(banner_image=banner_image.id)
            banner.banner_image = banner_image

        form = BannerForm(banner_form_data, instance=banner)
        if form.is_valid():
            form.save()
            messages.success(request, "Banner updated")
            return redirect('home')
    else:
        form = BannerForm(instance=banner)

    return render(request, 'homepage/banners/edit_banner.html', {
        'banner': banner,
        'form': form,
        'image_form': BannerImageForm(prefix='bannerimageform')
    })


@writeable_site_required
def delete_banner(request, banner_id):
    if not request.user.has_perm('homepage.delete_banner'):
        return redirect('home')

    banner = get_object_or_404(Banner, id=banner_id)

    if request.method == 'POST':
        if request.POST.get('yes'):
            banner.delete()
            messages.success(request, "Banner deleted")
            return redirect('home')
        else:
            return redirect('edit_banner', banner_id)
    else:
        return simple_ajax_confirmation(request,
            reverse('delete_banner', args=[banner_id]),
            "Are you sure you want to delete this banner?",
            html_title="Deleting banner: %s" % banner.title)


def browse_images(request):
    if not request.user.has_perm('homepage.change_banner'):
        return redirect('home')
    images = BannerImage.objects.order_by('-created_at')

    return render_modal_workflow(
        request,
        'homepage/banners/browse_images.html', 'homepage/banners/browse_images.js',
        {
            'images': images,
        }
    )
