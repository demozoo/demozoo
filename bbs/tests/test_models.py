from django.test import TestCase

from bbs.models import BBS


class TestBBS(TestCase):
    fixtures = ['tests/gasman.json']

    def test_str(self):
        bbs = BBS.objects.get(name='StarPort')
        self.assertEqual(str(bbs), 'StarPort')

    def test_absolute_url(self):
        bbs = BBS.objects.get(name='StarPort')
        self.assertEqual(bbs.get_absolute_url(), '/bbs/%d/' % bbs.id)
