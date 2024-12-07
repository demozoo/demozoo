from io import BytesIO

import PIL.Image
from django.contrib.auth.models import User
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from demoscene.tests.utils import MediaTestMixin
from homepage.models import Banner, BannerImage


def get_test_image():
    f = BytesIO()
    image = PIL.Image.new("RGBA", (200, 200), "white")
    image.save(f, "PNG")
    return ImageFile(f, name="test.png")


class TestBannerIndex(TestCase):
    def test_non_superuser(self):
        User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

        response = self.client.get("/banners/")
        self.assertRedirects(response, "/")

    def test_get(self):
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.client.login(username="testsuperuser", password="12345")

        response = self.client.get("/banners/")
        self.assertEqual(response.status_code, 200)


class TestAddBanner(MediaTestMixin, TestCase):
    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")

    def test_non_superuser(self):
        self.client.login(username="testuser", password="12345")

        response = self.client.get("/banners/new/")
        self.assertRedirects(response, "/")

    def test_get(self):
        self.client.login(username="testsuperuser", password="12345")

        response = self.client.get("/banners/new/")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(username="testsuperuser", password="12345")

        response = self.client.post(
            "/banners/new/",
            {
                "bannerimageform-image": SimpleUploadedFile("test.png", get_test_image().file.getvalue()),
                "title": "A new banner",
                "text": "good, isn't it?",
                "url": "https://pouet.net/",
                "show_for_anonymous_users": "1",
                "show_for_logged_in_users": "1",
            },
        )
        self.assertRedirects(response, "/")
        self.assertTrue(Banner.objects.filter(title="A new banner").exists())


class TestEditBanner(MediaTestMixin, TestCase):
    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")

        self.banner_image = BannerImage.objects.create(image=get_test_image())
        self.banner = Banner.objects.create(
            banner_image=self.banner_image,
            title="A new banner",
            text="good, isn't it?",
            url="https://pouet.net/",
            show_for_anonymous_users=True,
            show_for_logged_in_users=True,
        )

    def test_non_superuser(self):
        self.client.login(username="testuser", password="12345")

        response = self.client.get("/banners/%d/edit/" % self.banner.id)
        self.assertRedirects(response, "/")

    def test_get(self):
        self.client.login(username="testsuperuser", password="12345")

        response = self.client.get("/banners/%d/edit/" % self.banner.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(username="testsuperuser", password="12345")

        response = self.client.post(
            "/banners/%d/edit/" % self.banner.id,
            {
                "bannerimageform-image": SimpleUploadedFile("test.png", get_test_image().file.getvalue()),
                "title": "An edited banner",
                "text": "good, isn't it?",
                "url": "https://pouet.net/",
                "show_for_anonymous_users": "1",
                "show_for_logged_in_users": "1",
            },
        )
        self.assertRedirects(response, "/")
        self.assertTrue(Banner.objects.filter(title="An edited banner").exists())


class TestDeleteBanner(MediaTestMixin, TestCase):
    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")

        self.banner_image = BannerImage.objects.create(image=get_test_image())
        self.banner = Banner.objects.create(
            banner_image=self.banner_image,
            title="A new banner",
            text="good, isn't it?",
            url="https://pouet.net/",
            show_for_anonymous_users=True,
            show_for_logged_in_users=True,
        )

    def test_non_superuser(self):
        self.client.login(username="testuser", password="12345")

        response = self.client.get("/banners/%d/delete/" % self.banner.id)
        self.assertRedirects(response, "/")

    def test_get(self):
        self.client.login(username="testsuperuser", password="12345")

        response = self.client.get("/banners/%d/delete/" % self.banner.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(username="testsuperuser", password="12345")

        response = self.client.post(
            "/banners/%d/delete/" % self.banner.id,
            {
                "yes": "yes",
            },
        )
        self.assertRedirects(response, "/")
        self.assertFalse(Banner.objects.filter(title="A new banner").exists())

    def test_post_no_confirm(self):
        self.client.login(username="testsuperuser", password="12345")

        response = self.client.post(
            "/banners/%d/delete/" % self.banner.id,
            {
                "no": "no",
            },
        )
        self.assertRedirects(response, "/banners/%d/edit/" % self.banner.id)
        self.assertTrue(Banner.objects.filter(title="A new banner").exists())


class TestBrowseImages(MediaTestMixin, TestCase):
    def setUp(self):
        User.objects.create_user(username="testuser", password="12345")
        User.objects.create_superuser(username="testsuperuser", email="testsuperuser@example.com", password="12345")
        self.banner_image = BannerImage.objects.create(image=get_test_image())

    def test_non_superuser(self):
        self.client.login(username="testuser", password="12345")

        response = self.client.get("/banners/browse_images/")
        self.assertRedirects(response, "/")

    def test_get(self):
        self.client.login(username="testsuperuser", password="12345")

        response = self.client.get("/banners/browse_images/")
        self.assertEqual(response.status_code, 200)
