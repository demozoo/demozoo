# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from six.moves import urllib

from django.contrib import auth
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation 
from django.test import TestCase
from mock import patch

from demoscene.models import SceneID


class TestLogin(TestCase):
    def assertURLEqual(self, url1, url2, msg_prefix=''):
        # borrowed from django.test.testcases - can remove when we're on
        # django 2.2
        """
        Assert that two URLs are the same, ignoring the order of query string
        parameters except for parameters with the same name.
        For example, /path/?x=1&y=2 is equal to /path/?y=2&x=1, but
        /path/?a=1&a=2 isn't equal to /path/?a=2&a=1.
        """
        def normalize(url):
            """Sort the URL's query string parameters."""
            url = str(url)  # Coerce reverse_lazy() URLs.
            scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url)
            query_parts = sorted(urllib.parse.parse_qsl(query))
            return urllib.parse.urlunparse((scheme, netloc, path, params, urllib.parse.urlencode(query_parts), fragment))

        self.assertEqual(
            normalize(url1), normalize(url2),
            msg_prefix + "Expected '%s' to equal '%s'." % (url1, url2)
        )

    @patch('sceneid.auth.get_random_string')
    def test_login_new_user(self, get_random_string):
        get_random_string.return_value = '66666666'
        response = self.client.get('/account/sceneid/auth/?next=/music/')
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(
            response['Location'],
            'https://id.scene.org/oauth/authorize/?state=66666666&redirect_uri=https%3A%2F%2Fdemozoo.org%2Faccount%2Fsceneid%2Flogin%2F&response_type=code&client_id=SCENEID_K3Y'
        )

        response = self.client.get('/account/sceneid/login/?state=55555555&code=123')
        self.assertEqual(response.status_code, 400)

        # successful login but no known record on Demozoo - prompt to connect
        response = self.client.get('/account/sceneid/login/?state=66666666&code=123')
        self.assertRedirects(response, '/account/sceneid/connect/')
        sceneid_data = self.client.session['sceneid_login_userdata']
        self.assertEqual(sceneid_data['display_name'], 'gasman')
        self.assertEqual(sceneid_data['id'], 2260)

        # create new account
        response = self.client.post('/account/sceneid/connect/', {
            'accountNew': "Register new account",
            'username': "newuser",
            'email': "newuser@example.com"
        })
        self.assertRedirects(response, '/')
        logged_in_user = auth.get_user(self.client)
        self.assertTrue(logged_in_user.is_authenticated())
        self.assertEqual(logged_in_user.username, 'newuser')
        self.assertEqual(SceneID.objects.get(user=logged_in_user).sceneid, 2260)

        logged_in_user.delete()
        self.assertFalse(auth.get_user(self.client).is_authenticated())

    @patch('sceneid.auth.get_random_string')
    def test_login_new_user_with_previous_session(self, get_random_string):
        testuser = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        get_random_string.return_value = '66666666'
        response = self.client.get('/account/sceneid/auth/?next=/music/')
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(
            response['Location'],
            'https://id.scene.org/oauth/authorize/?state=66666666&redirect_uri=https%3A%2F%2Fdemozoo.org%2Faccount%2Fsceneid%2Flogin%2F&response_type=code&client_id=SCENEID_K3Y'
        )

        response = self.client.get('/account/sceneid/login/?state=55555555&code=123')
        self.assertEqual(response.status_code, 400)

        # successful login but no known record on Demozoo - prompt to connect
        response = self.client.get('/account/sceneid/login/?state=66666666&code=123')
        self.assertRedirects(response, '/account/sceneid/connect/')
        sceneid_data = self.client.session['sceneid_login_userdata']
        self.assertEqual(sceneid_data['display_name'], 'gasman')
        self.assertEqual(sceneid_data['id'], 2260)

        # create new account
        response = self.client.post('/account/sceneid/connect/', {
            'accountNew': "Register new account",
            'username': "newuser",
            'email': "newuser@example.com"
        })
        self.assertRedirects(response, '/')
        logged_in_user = auth.get_user(self.client)
        self.assertTrue(logged_in_user.is_authenticated())
        self.assertEqual(logged_in_user.username, 'newuser')
        self.assertNotEqual(logged_in_user, testuser)
        self.assertEqual(SceneID.objects.get(user=logged_in_user).sceneid, 2260)

    @patch('sceneid.auth.get_random_string')
    def test_login_connect_user(self, get_random_string):
        testuser = User.objects.create_user(username='testuser', password='12345')

        get_random_string.return_value = '66666666'
        response = self.client.get('/account/sceneid/auth/?next=/music/')
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(
            response['Location'],
            'https://id.scene.org/oauth/authorize/?state=66666666&redirect_uri=https%3A%2F%2Fdemozoo.org%2Faccount%2Fsceneid%2Flogin%2F&response_type=code&client_id=SCENEID_K3Y'
        )

        response = self.client.get('/account/sceneid/login/?state=55555555&code=123')
        self.assertEqual(response.status_code, 400)

        # successful login but no known record on Demozoo - prompt to connect
        response = self.client.get('/account/sceneid/login/?state=66666666&code=123')
        self.assertRedirects(response, '/account/sceneid/connect/')
        sceneid_data = self.client.session['sceneid_login_userdata']
        self.assertEqual(sceneid_data['display_name'], 'gasman')
        self.assertEqual(sceneid_data['id'], 2260)

        # log in to testuser account
        response = self.client.post('/account/sceneid/connect/', {
            'accountExisting': "Log in",
            'username': "testuser",
            'password': "12345"
        })
        self.assertRedirects(response, '/')
        logged_in_user = auth.get_user(self.client)
        self.assertEqual(logged_in_user, testuser)
        self.assertEqual(SceneID.objects.get(user=testuser).sceneid, 2260)

    @patch('sceneid.auth.get_random_string')
    def test_login_connect_user_bad_login(self, get_random_string):
        testuser = User.objects.create_user(username='testuser', password='12345')

        get_random_string.return_value = '66666666'
        response = self.client.get('/account/sceneid/auth/?next=/music/')
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(
            response['Location'],
            'https://id.scene.org/oauth/authorize/?state=66666666&redirect_uri=https%3A%2F%2Fdemozoo.org%2Faccount%2Fsceneid%2Flogin%2F&response_type=code&client_id=SCENEID_K3Y'
        )

        response = self.client.get('/account/sceneid/login/?state=55555555&code=123')
        self.assertEqual(response.status_code, 400)

        # successful login but no known record on Demozoo - prompt to connect
        response = self.client.get('/account/sceneid/login/?state=66666666&code=123')
        self.assertRedirects(response, '/account/sceneid/connect/')
        sceneid_data = self.client.session['sceneid_login_userdata']
        self.assertEqual(sceneid_data['display_name'], 'gasman')
        self.assertEqual(sceneid_data['id'], 2260)

        # log in to testuser account
        response = self.client.post('/account/sceneid/connect/', {
            'accountExisting': "Log in",
            'username': "testuser",
            'password': "12346"
        })
        self.assertEqual(response.status_code, 200)
        logged_in_user = auth.get_user(self.client)
        self.assertFalse(logged_in_user.is_authenticated())
        self.assertFalse(SceneID.objects.filter(user=testuser).exists())

    @patch('sceneid.auth.get_random_string')
    def test_login_existing_user(self, get_random_string):
        testuser = User.objects.create_user(username='testuser', password='12345')
        SceneID.objects.create(user=testuser, sceneid=2260)

        get_random_string.return_value = '66666666'
        response = self.client.get('/account/sceneid/auth/?next=/music/')
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(
            response['Location'],
            'https://id.scene.org/oauth/authorize/?state=66666666&redirect_uri=https%3A%2F%2Fdemozoo.org%2Faccount%2Fsceneid%2Flogin%2F&response_type=code&client_id=SCENEID_K3Y'
        )

        response = self.client.get('/account/sceneid/login/?state=55555555&code=123')
        self.assertEqual(response.status_code, 400)

        # successful login and known user on Demozoo
        response = self.client.get('/account/sceneid/login/?state=66666666&code=123')
        self.assertRedirects(response, '/music/')
        logged_in_user = auth.get_user(self.client)
        self.assertEqual(logged_in_user, testuser)

    @patch('sceneid.auth.get_random_string')
    def test_login_banned_user(self, get_random_string):
        testuser = User.objects.create_user(username='testuser', password='12345')
        testuser.is_active = False
        testuser.save()
        SceneID.objects.create(user=testuser, sceneid=2260)

        get_random_string.return_value = '66666666'
        response = self.client.get('/account/sceneid/auth/?next=/music/')
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(
            response['Location'],
            'https://id.scene.org/oauth/authorize/?state=66666666&redirect_uri=https%3A%2F%2Fdemozoo.org%2Faccount%2Fsceneid%2Flogin%2F&response_type=code&client_id=SCENEID_K3Y'
        )

        response = self.client.get('/account/sceneid/login/?state=55555555&code=123')
        self.assertEqual(response.status_code, 400)

        # login rejected due to is_active=False
        response = self.client.get('/account/sceneid/login/?state=66666666&code=123')
        self.assertRedirects(response, '/music/')
        logged_in_user = auth.get_user(self.client)
        self.assertFalse(logged_in_user.is_authenticated())

    def test_connect_without_login(self):
        response = self.client.get('/account/sceneid/connect/')
        self.assertRedirects(response, '/account/login/')


class TestAuth(TestCase):
    def test_auth(self):
        self.assertFalse(auth.authenticate(sceneid=None))
