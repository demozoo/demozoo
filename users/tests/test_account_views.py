import re

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core import mail
from django.test import TestCase

from demoscene.models import CaptchaQuestion


class TestLogin(TestCase):
    def test_login_banned_ip(self):
        response = self.client.get("/account/login/", REMOTE_ADDR="81.234.236.23")
        self.assertRedirects(response, "/")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Your account was disabled.")

    def test_get(self):
        response = self.client.get("/account/login/")
        self.assertEqual(response.status_code, 200)

    def test_registration_banned_ip(self):
        response = self.client.get("/account/login/", REMOTE_ADDR="109.196.230.41")
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        response = self.client.post(
            "/account/login/",
            {
                "username": "testuser",
                "password": "12345",
            },
        )
        self.assertRedirects(response, "/")

    def test_post_disabled(self):
        self.user = User.objects.create_user(username="testuser", password="12345", is_active=False)
        response = self.client.post(
            "/account/login/",
            {
                "username": "testuser",
                "password": "12345",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your username and password didn't match. Please try again.")


class TestAccountIndex(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")

    def test_account_index(self):
        response = self.client.get("/account/")
        self.assertRedirects(response, "/account/login/?next=/account/")

        self.client.login(username="testuser", password="12345")
        response = self.client.get("/account/")
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username="testuser")
        user.is_active = False
        user.save()
        response = self.client.get("/account/")
        self.assertRedirects(response, "/account/login/?next=/account/")


class TestSignup(TestCase):
    def setUp(self):
        self.captcha = CaptchaQuestion.objects.create(question="How many legs do cows have?", answer="Four")

    def test_login_banned_ip(self):
        response = self.client.get("/account/signup/", REMOTE_ADDR="81.234.236.23")
        self.assertRedirects(response, "/")

    def test_registration_banned_ip(self):
        response = self.client.get("/account/signup/", REMOTE_ADDR="109.196.230.41")
        self.assertRedirects(response, "/")

    def test_signup(self):
        response = self.client.get("/account/signup/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/account/signup/",
            {
                "username": "bob",
                "email": "bob@example.com",
                "password1": "b0bb0bb0b",
                "password2": "b0bb0bb0b",
                "captcha": "four",
            },
        )
        self.assertRedirects(response, "/")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Account created")
        self.assertEqual(1, User.objects.filter(username="bob").count())


class TestChangePassword(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_change_password(self):
        response = self.client.get("/account/change_password/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/account/change_password/",
            {
                "old_password": "12345",
                "new_password1": "67890",
                "new_password2": "67890",
            },
        )
        self.assertRedirects(response, "/")
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Password updated")

        self.assertTrue(self.client.login(username="testuser", password="67890"))


class TestResetPassword(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="testuser@example.com", password="12345")

    def test_reset_password(self):
        response = self.client.get("/account/forgotten_password/")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/account/forgotten_password/",
            {
                "email": "testuser@example.com",
            },
        )
        self.assertRedirects(response, "/account/forgotten_password/success/")

        response = self.client.get("/account/forgotten_password/success/")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["testuser@example.com"])
        reset_url = re.search(r"/account/forgotten_password/\S+", mail.outbox[0].body).group(0)
        uid = re.match(r"^/account/forgotten_password/check/([^\/]+)/", reset_url).group(1)

        response = self.client.get("/account/forgotten_password/check/AAAA/AAAA-AAAAAAAA/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password reset link is not valid")

        response = self.client.get(reset_url)
        check_ok_url = "/account/forgotten_password/check/%s/set-password/" % uid
        self.assertRedirects(response, check_ok_url)

        response = self.client.get(check_ok_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reset password")

        response = self.client.post(
            check_ok_url,
            {
                "new_password1": "b3tt3rpassw0rd!!!",
                "new_password2": "b3tt3rpassw0rd!!!",
            },
        )
        self.assertRedirects(response, "/account/forgotten_password/done/")

        response = self.client.get("/account/forgotten_password/done/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password change successful")

        self.assertTrue(self.client.login(username="testuser", password="b3tt3rpassw0rd!!!"))


class TestLogout(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_logout(self):
        response = self.client.post("/account/logout/")
        self.assertRedirects(response, "/")

        response = self.client.get("/account/")
        self.assertRedirects(response, "/account/login/?next=/account/")
