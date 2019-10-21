from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase

from demoscene.models import CaptchaQuestion


class TestLogin(TestCase):
    def test_banned_ip(self):
        response = self.client.get('/account/login/', REMOTE_ADDR='81.234.236.23')
        self.assertRedirects(response, '/')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Your account was disabled.")

    def test_get(self):
        response = self.client.get('/account/login/')
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        response = self.client.post('/account/login/', {
            'username': 'testuser',
            'password': '12345',
        })
        self.assertRedirects(response, '/')

    def test_post_disabled(self):
        self.user = User.objects.create_user(username='testuser', password='12345', is_active=False)
        response = self.client.post('/account/login/', {
            'username': 'testuser',
            'password': '12345',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your username and password didn't match. Please try again.")


class TestAccountIndex(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_account_index(self):
        response = self.client.get('/account/')
        self.assertRedirects(response, '/account/login/?next=/account/')

        self.client.login(username='testuser', password='12345')
        response = self.client.get('/account/')
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username='testuser')
        user.is_active = False
        user.save()
        response = self.client.get('/account/')
        self.assertRedirects(response, '/account/login/?next=/account/')


class TestSignup(TestCase):
    def setUp(self):
        self.captcha = CaptchaQuestion.objects.create(
            question="How many legs do cows have?",
            answer="Four"
        )

    def test_banned_ip(self):
        response = self.client.get('/account/signup/', REMOTE_ADDR='81.234.236.23')
        self.assertRedirects(response, '/')

    def test_signup(self):
        response = self.client.get('/account/signup/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/account/signup/', {
            'username': 'bob',
            'email': 'bob@example.com',
            'password1': 'b0bb0bb0b',
            'password2': 'b0bb0bb0b',
            'captcha': 'four'
        })
        self.assertRedirects(response, '/')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Account created")
        self.assertEqual(1, User.objects.filter(username='bob').count())


class TestChangePassword(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_change_password(self):
        response = self.client.get('/account/change_password/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/account/change_password/', {
            'old_password': '12345',
            'new_password1': '67890',
            'new_password2': '67890',
        })
        self.assertRedirects(response, '/')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Password updated")

        self.assertTrue(self.client.login(username='testuser', password='67890'))
