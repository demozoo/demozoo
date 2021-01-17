from django.test import TestCase

from bbs.models import BBS, Operator


class TestBBS(TestCase):
    fixtures = ['tests/gasman.json']

    def test_str(self):
        bbs = BBS.objects.get(name='StarPort')
        self.assertEqual(str(bbs), 'StarPort')

    def test_absolute_url(self):
        bbs = BBS.objects.get(name='StarPort')
        self.assertEqual(bbs.get_absolute_url(), '/bbs/%d/' % bbs.id)


class TestOperator(TestCase):
    fixtures = ['tests/gasman.json']

    def test_str(self):
        operator = Operator.objects.get(bbs__name='StarPort', releaser__name='Abyss')
        self.assertEqual(str(operator), 'Abyss - sysop of StarPort')
