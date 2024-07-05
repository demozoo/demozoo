from io import BytesIO

import PIL.Image
from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from demoscene.tests.utils import MediaTestMixin
from homepage.models import NewsImage, NewsStory


def get_test_image():
    f = BytesIO()
    image = PIL.Image.new('RGBA', (200, 200), 'white')
    image.save(f, 'PNG')
    return ImageFile(f, name='test.png')


class TestNewsIndex(MediaTestMixin, TestCase):
    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')

        self.image = NewsImage.objects.create(image=get_test_image())
        self.news_story = NewsStory.objects.create(
            image=self.image,
            title="Those are the headlines",
            text="God I wish they weren't.",
            is_public=True
        )

    def test_get(self):
        response = self.client.get('/news/')
        self.assertEqual(response.status_code, 200)

    def test_pagination_out_of_range(self):
        response = self.client.get('/news/', {'page': 999})
        self.assertEqual(response.status_code, 200)


class TestAddNews(MediaTestMixin, TestCase):
    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')

    def test_non_superuser(self):
        self.client.login(username='testuser', password='12345')

        response = self.client.get('/news/new/')
        self.assertRedirects(response, '/')

    def test_get(self):
        self.client.login(username='testsuperuser', password='12345')

        response = self.client.get('/news/new/')
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(username='testsuperuser', password='12345')

        response = self.client.post('/news/new/', {
            'news_image-image': SimpleUploadedFile('test.png', get_test_image().file.getvalue()),
            'title': 'Those are the headlines',
            'text': "God I wish they weren't.",
            'is_public': '1',
        })
        self.assertRedirects(response, '/')
        self.assertTrue(NewsStory.objects.filter(title='Those are the headlines').exists())


class TestEditNews(MediaTestMixin, TestCase):
    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')

        self.image = NewsImage.objects.create(image=get_test_image())
        self.news_story = NewsStory.objects.create(
            image=self.image,
            title="Those are the headlines",
            text="God I wish they weren't.",
            is_public=True
        )

    def test_non_superuser(self):
        self.client.login(username='testuser', password='12345')

        response = self.client.get('/news/%d/edit/' % self.news_story.id)
        self.assertRedirects(response, '/')

    def test_get(self):
        self.client.login(username='testsuperuser', password='12345')

        response = self.client.get('/news/%d/edit/' % self.news_story.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(username='testsuperuser', password='12345')

        response = self.client.post('/news/%d/edit/' % self.news_story.id, {
            'news_image-image': SimpleUploadedFile('test.png', get_test_image().file.getvalue()),
            'title': "Those are the edited headlines",
            'text': "God I wish they weren't.",
            'is_public': '1',
        })
        self.assertRedirects(response, '/')
        self.assertTrue(NewsStory.objects.filter(title='Those are the edited headlines').exists())


class TestDeleteNews(MediaTestMixin, TestCase):
    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')

        self.image = NewsImage.objects.create(image=get_test_image())
        self.news_story = NewsStory.objects.create(
            image=self.image,
            title="Peter, you've lost the news!",
            text="Sorry.",
            is_public=True,
        )

    def test_non_superuser(self):
        self.client.login(username='testuser', password='12345')

        response = self.client.get('/news/%d/delete/' % self.news_story.id)
        self.assertRedirects(response, '/')

    def test_get(self):
        self.client.login(username='testsuperuser', password='12345')

        response = self.client.get('/news/%d/delete/' % self.news_story.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(username='testsuperuser', password='12345')

        response = self.client.post('/news/%d/delete/' % self.news_story.id, {
            'yes': 'yes',
        })
        self.assertRedirects(response, '/')
        self.assertFalse(NewsStory.objects.filter(title="Peter, you've lost the news!").exists())

    def test_post_no_confirm(self):
        self.client.login(username='testsuperuser', password='12345')

        response = self.client.post('/news/%d/delete/' % self.news_story.id, {
            'no': 'no',
        })
        self.assertRedirects(response, '/news/%d/edit/' % self.news_story.id)
        self.assertTrue(NewsStory.objects.filter(title="Peter, you've lost the news!").exists())


class TestBrowseImages(MediaTestMixin, TestCase):
    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.image = NewsImage.objects.create(image=get_test_image())

    def test_non_superuser(self):
        self.client.login(username='testuser', password='12345')

        response = self.client.get('/news/browse_images/')
        self.assertRedirects(response, '/')

    def test_get(self):
        self.client.login(username='testsuperuser', password='12345')

        response = self.client.get('/news/browse_images/')
        self.assertEqual(response.status_code, 200)
