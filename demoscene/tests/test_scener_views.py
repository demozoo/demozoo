from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from demoscene.models import Edit, Membership, Releaser


class TestScenersIndex(TestCase):
    fixtures = ['tests/gasman.json']

    def test_get(self):
        response = self.client.get('/sceners/')
        self.assertEqual(response.status_code, 200)


class TestShowScener(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.raww_arse = Releaser.objects.get(name='Raww Arse')
        self.gasman = Releaser.objects.get(name='Gasman')

    def test_get(self):
        response = self.client.get('/sceners/%d/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)

    def test_redirect_to_group(self):
        response = self.client.get('/sceners/%d/' % self.raww_arse.id)
        self.assertRedirects(response, '/groups/%d/' % self.raww_arse.id)

    def test_get_history(self):
        response = self.client.get('/sceners/%d/history/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)


class TestCreateScener(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_get(self):
        response = self.client.get('/sceners/new/')
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/sceners/new/', {
            'name': 'Sir Garbagetruck',
            'nick_variant_list': '',
        })
        truck = Releaser.objects.get(name='Sir Garbagetruck')
        self.assertRedirects(response, '/sceners/%d/' % truck.id)


class TestEditLocation(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.yerzmyey = Releaser.objects.get(name='Yerzmyey')

    def test_locked(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/sceners/%d/edit_location/' % self.yerzmyey.id)
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/sceners/%d/edit_location/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post('/sceners/%d/edit_location/' % self.gasman.id, {
            'location': "Oxford",
        })
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(Releaser.objects.get(name='Gasman').location, "Oxford, Oxfordshire, England, United Kingdom")


class TestEditRealName(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')

    def test_non_superuser(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/sceners/%d/edit_real_name/' % self.gasman.id)
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)

    def test_get(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.get('/sceners/%d/edit_real_name/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.post('/sceners/%d/edit_real_name/' % self.gasman.id, {
            'first_name': "Matt",
            'show_first_name': True,
            'surname': "Gustavsson",
            'real_name_note': "yes really",
        })
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(Releaser.objects.get(name='Gasman').surname, "Gustavsson")


class TestAddGroup(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.yerzmyey = Releaser.objects.get(name='Yerzmyey')
        self.limp_ninja = Releaser.objects.create(name='Limp Ninja', is_group=True)

    def test_locked(self):
        response = self.client.get('/sceners/%d/add_group/' % self.yerzmyey.id)
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get('/sceners/%d/add_group/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/sceners/%d/add_group/' % self.gasman.id, {
            'group_nick_search': 'limp ninja',
            'group_nick_match_id': self.limp_ninja.primary_nick.id,
            'group_nick_match_name': 'limp ninja',
            'is_current': 'on'
        })
        self.assertRedirects(response, '/sceners/%d/?editing=groups' % self.gasman.id)
        self.assertEqual(1, Membership.objects.filter(member=self.gasman, group=self.limp_ninja).count())


class TestRemoveGroup(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.yerzmyey = Releaser.objects.get(name='Yerzmyey')
        self.hooy_program = Releaser.objects.get(name='Hooy-Program')

    def test_locked(self):
        response = self.client.get('/sceners/%d/remove_group/%d/' % (self.yerzmyey.id, self.hooy_program.id))
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get('/sceners/%d/remove_group/%d/' % (self.gasman.id, self.hooy_program.id))
        self.assertEqual(response.status_code, 200)

    def test_ex_member(self):
        response = self.client.post('/sceners/%d/remove_group/%d/' % (self.gasman.id, self.hooy_program.id), {
            'deletion_type': 'ex_member',
        })
        self.assertRedirects(response, '/sceners/%d/?editing=groups' % self.gasman.id)
        self.assertFalse(Membership.objects.get(member=self.gasman, group=self.hooy_program).is_current)

    def test_remove(self):
        response = self.client.post('/sceners/%d/remove_group/%d/' % (self.gasman.id, self.hooy_program.id), {
            'deletion_type': 'full',
        })
        self.assertRedirects(response, '/sceners/%d/?editing=groups' % self.gasman.id)
        self.assertEqual(Membership.objects.filter(member=self.gasman, group=self.hooy_program).count(), 0)

    def test_post_invalid(self):
        response = self.client.post('/sceners/%d/remove_group/%d/' % (self.gasman.id, self.hooy_program.id), {
            'deletion_type': 'blah',
        })
        self.assertEqual(response.status_code, 200)


class TestEditMembership(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.yerzmyey = Releaser.objects.get(name='Yerzmyey')
        self.hooy_program = Releaser.objects.get(name='Hooy-Program')

    def test_locked(self):
        membership = Membership.objects.get(member=self.yerzmyey, group=self.hooy_program)
        response = self.client.get('/sceners/%d/edit_membership/%d/' % (self.yerzmyey.id, membership.id))
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        membership = Membership.objects.get(member=self.gasman, group=self.hooy_program)
        response = self.client.get('/sceners/%d/edit_membership/%d/' % (self.gasman.id, membership.id))
        self.assertEqual(response.status_code, 200)

    def test_post_make_ex_member(self):
        membership = Membership.objects.get(member=self.gasman, group=self.hooy_program)
        response = self.client.post('/sceners/%d/edit_membership/%d/' % (self.gasman.id, membership.id), {
            'group_nick_search': 'hooy-program',
            'group_nick_match_id': self.hooy_program.primary_nick.id,
            'group_nick_match_name': 'hooy-program',
        })
        self.assertRedirects(response, '/sceners/%d/?editing=groups' % self.gasman.id)
        self.assertFalse(Membership.objects.get(member=self.gasman, group=self.hooy_program).is_current)
        edit = Edit.for_model(self.gasman, True).first()
        self.assertIn("set as ex-member", edit.description)

    def test_post_make_current_member(self):
        membership = Membership.objects.get(member=self.gasman, group=self.hooy_program)
        membership.is_current = False
        membership.save()

        response = self.client.post('/sceners/%d/edit_membership/%d/' % (self.gasman.id, membership.id), {
            'group_nick_search': 'hooy-program',
            'group_nick_match_id': self.hooy_program.primary_nick.id,
            'group_nick_match_name': 'hooy-program',
            'is_current': 'is_current',
        })
        self.assertRedirects(response, '/sceners/%d/?editing=groups' % self.gasman.id)
        self.assertTrue(Membership.objects.get(member=self.gasman, group=self.hooy_program).is_current)
        edit = Edit.for_model(self.gasman, True).first()
        self.assertIn("set as current member", edit.description)


class TestConvertToGroup(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser', email='testuser@example.com', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.laesq = Releaser.objects.get(name='LaesQ')

    def test_unconvertable(self):
        response = self.client.get('/sceners/%d/convert_to_group/' % self.gasman.id)
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)

    def test_get(self):
        response = self.client.get('/sceners/%d/convert_to_group/' % self.laesq.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/sceners/%d/convert_to_group/' % self.laesq.id, {
            'yes': 'yes',
        })
        self.assertRedirects(response, '/groups/%d/' % self.laesq.id)
        self.assertTrue(Releaser.objects.get(name='LaesQ').is_group)
