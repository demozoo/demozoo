from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from forums.models import Topic


class TestTopicModel(TestCase):
    fixtures = ['tests/forum.json']

    def test_str(self):
        topic = Topic.objects.get(title="fix me beautifull")
        self.assertEqual(str(topic), "fix me beautifull")
