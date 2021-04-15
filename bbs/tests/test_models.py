from django.test import TestCase

from bbs.models import BBS, Affiliation, Operator


class TestBBS(TestCase):
    fixtures = ['tests/gasman.json']

    def test_str(self):
        bbs = BBS.objects.get(name='StarPort')
        self.assertEqual(str(bbs), 'StarPort')

    def test_absolute_url(self):
        bbs = BBS.objects.get(name='StarPort')
        self.assertEqual(bbs.get_absolute_url(), '/bbs/%d/' % bbs.id)

    def test_primary_name(self):
        bbs = BBS.objects.get(name='StarPort')
        self.assertEqual(bbs.primary_name.name, 'StarPort')
        self.assertEqual(str(bbs.primary_name), 'StarPort')
        self.assertTrue(bbs.primary_name.is_primary_name())

    def test_asciified_name(self):
        bbs = BBS.objects.get(name='StarPort')
        self.assertEqual(bbs.asciified_name, 'StarPort')

    def test_update_name(self):
        bbs = BBS.objects.get(name='StarPort')
        name = bbs.primary_name
        name.name = 'also starport'
        name.save()
        self.assertEqual(bbs.name, 'also starport')


class TestOperator(TestCase):
    fixtures = ['tests/gasman.json']

    def test_str(self):
        operator = Operator.objects.get(bbs__name='StarPort', releaser__name='Abyss')
        self.assertEqual(str(operator), 'Abyss - sysop of StarPort')


class TestAffiliation(TestCase):
    fixtures = ['tests/gasman.json']

    def test_str(self):
        affiliation = Affiliation.objects.get(bbs__name='StarPort', group__name='Future Crew')
        self.assertEqual(str(affiliation), 'StarPort - WHQ for Future Crew')
        affiliation.role = None
        self.assertEqual(str(affiliation), 'Future Crew affiliated with StarPort')
