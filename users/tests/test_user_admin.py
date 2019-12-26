from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase


class TestUserAdmin(TestCase):
    def test_no_delete_link(self):
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        other_user = User.objects.create_user(username='otheruser', email='otheruser@example.com', password='12345')
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.get('/admin/auth/user/%d/change/' % other_user.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'class="deletelink"')
