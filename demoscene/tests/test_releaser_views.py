from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from demoscene.models import Nick, Releaser, ReleaserExternalLink
from productions.models import Credit, Production


class TestAddCredit(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.laesq = Releaser.objects.get(name='LaesQ')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_locked(self):
        response = self.client.get('/releasers/%d/add_credit/' % self.papaya_dezign.id)
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get('/releasers/%d/add_credit/' % self.laesq.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/releasers/%d/add_credit/' % self.laesq.id, {
            'nick': self.laesq.primary_nick.id,
            'production_name': 'Pondlife',
            'production_id': self.pondlife.id,
            'credit-TOTAL_FORMS': 1,
            'credit-INITIAL_FORMS': 0,
            'credit-MIN_NUM_FORMS': 0,
            'credit-MAX_NUM_FORMS': 1000,
            'credit-0-category': 'Music',
            'credit-0-role': '',
        })
        self.assertRedirects(response, '/sceners/%d/' % self.laesq.id)
        self.assertEqual(Credit.objects.filter(production=self.pondlife, nick=self.laesq.primary_nick).count(), 1)


class TestEditCredit(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_locked(self):
        response = self.client.get(
            '/releasers/%d/edit_credit/%d/%d/' % (self.papaya_dezign.id, self.papaya_dezign.primary_nick.id, self.pondlife.id)
        )
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get(
            '/releasers/%d/edit_credit/%d/%d/' % (self.gasman.id, self.gasman.primary_nick.id, self.pondlife.id)
        )
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        credit = Credit.objects.get(nick=self.gasman.primary_nick, production=self.pondlife)
        response = self.client.post(
            '/releasers/%d/edit_credit/%d/%d/' % (self.gasman.id, self.gasman.primary_nick.id, self.pondlife.id),
            {
                'nick': self.gasman.primary_nick.id,
                'production_name': 'Pondlife',
                'production_id': self.pondlife.id,
                'credit-TOTAL_FORMS': 1,
                'credit-INITIAL_FORMS': 1,
                'credit-MIN_NUM_FORMS': 0,
                'credit-MAX_NUM_FORMS': 1000,
                'credit-0-id': credit.id,
                'credit-0-category': 'Music',
                'credit-0-role': '',
            }
        )
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(Credit.objects.get(production=self.pondlife, nick=self.gasman.primary_nick).category, 'Music')


class TestDeleteCredit(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')
        self.pondlife = Production.objects.get(title='Pondlife')

    def test_locked(self):
        response = self.client.get(
            '/releasers/%d/delete_credit/%d/%d/' % (self.papaya_dezign.id, self.papaya_dezign.primary_nick.id, self.pondlife.id)
        )
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get(
            '/releasers/%d/delete_credit/%d/%d/' % (self.gasman.id, self.gasman.primary_nick.id, self.pondlife.id)
        )
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(
            '/releasers/%d/delete_credit/%d/%d/' % (self.gasman.id, self.gasman.primary_nick.id, self.pondlife.id),
            {'yes': 'yes'}
        )
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(Credit.objects.filter(production=self.pondlife, nick=self.gasman.primary_nick).count(), 0)


class TestEditNotes(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')

    def test_not_superuser(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/releasers/%d/edit_notes/' % self.gasman.id)
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)

    def test_get(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.get('/releasers/%d/edit_notes/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.post('/releasers/%d/edit_notes/' % self.gasman.id, {
            'notes': "the world's number 1 ZX Spectrum rockstar",
        })
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(
            Releaser.objects.get(name='Gasman').notes,
            "the world's number 1 ZX Spectrum rockstar"
        )


class TestEditNick(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.shingebis = Nick.objects.get(name='Shingebis')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')
        self.raww_arse = Releaser.objects.get(name='Raww Arse')

    def test_locked(self):
        npd = self.papaya_dezign.nicks.create(name='Not Papaya Design')
        response = self.client.get('/releasers/%d/edit_nick/%d/' % (self.papaya_dezign.id, npd.id))
        self.assertEqual(response.status_code, 403)

    def test_get_scener(self):
        response = self.client.get('/releasers/%d/edit_nick/%d/' % (self.gasman.id, self.shingebis.id))
        self.assertEqual(response.status_code, 200)

    def test_get_group(self):
        response = self.client.get('/releasers/%d/edit_nick/%d/' % (self.raww_arse.id, self.raww_arse.primary_nick.id))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/releasers/%d/edit_nick/%d/' % (self.gasman.id, self.shingebis.id), {
            'name': 'Shingebis',
            'nick_variant_list': '',
            'override_primary_nick': 'true',
        })
        self.assertRedirects(response, '/sceners/%d/?editing=nicks' % self.gasman.id)
        self.assertEqual(Releaser.objects.get(id=self.gasman.id).name, 'Shingebis')


class TestAddNick(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')
        self.raww_arse = Releaser.objects.get(name='Raww Arse')

    def test_locked(self):
        response = self.client.get('/releasers/%d/add_nick/' % self.papaya_dezign.id)
        self.assertEqual(response.status_code, 403)

    def test_get_scener(self):
        response = self.client.get('/releasers/%d/add_nick/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)

    def test_get_group(self):
        response = self.client.get('/releasers/%d/add_nick/' % self.raww_arse.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/releasers/%d/add_nick/' % self.gasman.id, {
            'name': 'dj.mo0nbug',
            'nick_variant_list': '',
            'override_primary_nick': 'true',
        })
        self.assertRedirects(response, '/sceners/%d/?editing=nicks' % self.gasman.id)
        self.assertEqual(Releaser.objects.get(id=self.gasman.id).name, 'dj.mo0nbug')


class TestEditPrimaryNick(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')

    def test_locked(self):
        response = self.client.get('/releasers/%d/edit_primary_nick/' % self.papaya_dezign.id)
        self.assertEqual(response.status_code, 403)

    def test_get_scener(self):
        response = self.client.get('/releasers/%d/edit_primary_nick/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)


class TestChangePrimaryNick(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.shingebis = Nick.objects.get(name='Shingebis')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')

    def test_locked(self):
        npd = self.papaya_dezign.nicks.create(name='Not Papaya Design')
        response = self.client.post('/releasers/%d/change_primary_nick/' % self.papaya_dezign.id, {
            'nick_id': npd.id,
        })
        self.assertEqual(response.status_code, 403)

    def test_post(self):
        response = self.client.post('/releasers/%d/change_primary_nick/' % self.gasman.id, {
            'nick_id': self.shingebis.id,
        })
        self.assertRedirects(response, '/sceners/%d/?editing=nicks' % self.gasman.id)
        self.assertEqual(Releaser.objects.get(id=self.gasman.id).name, 'Shingebis')


class TestDeleteNick(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.shingebis = Nick.objects.get(name='Shingebis')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')

    def test_locked(self):
        npd = self.papaya_dezign.nicks.create(name='Not Papaya Design')
        response = self.client.get('/releasers/%d/delete_nick/%d/' % (self.papaya_dezign.id, npd.id))
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get('/releasers/%d/delete_nick/%d/' % (self.gasman.id, self.shingebis.id))
        self.assertEqual(response.status_code, 200)

    def test_get_unreferenced(self):
        moonbug = self.gasman.nicks.create(name='dj.mo0nbug')
        response = self.client.get('/releasers/%d/delete_nick/%d/' % (self.gasman.id, moonbug.id))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post('/releasers/%d/delete_nick/%d/' % (self.gasman.id, self.shingebis.id), {
            'yes': 'yes',
        })
        self.assertRedirects(response, '/sceners/%d/?editing=nicks' % self.gasman.id)
        self.assertEqual(Nick.objects.filter(name='Shingebis').count(), 0)

    def test_cannot_delete_primary_nick(self):
        response = self.client.post('/releasers/%d/delete_nick/%d/' % (self.gasman.id, self.gasman.primary_nick.id), {
            'yes': 'yes',
        })
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(Nick.objects.filter(name='Gasman').count(), 1)


class TestDeleteReleaser(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.raww_arse = Releaser.objects.get(name='Raww Arse')

    def test_not_superuser(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/releasers/%d/delete/' % self.gasman.id)
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)

    def test_get(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.get('/releasers/%d/delete/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)

    def test_post_scener(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.post('/releasers/%d/delete/' % self.gasman.id, {
            'yes': 'yes',
        })
        self.assertEqual(Releaser.objects.filter(name='Gasman').count(), 0)
        self.assertRedirects(response, '/sceners/')

    def test_post_group(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.post('/releasers/%d/delete/' % self.raww_arse.id, {
            'yes': 'yes',
        })
        self.assertEqual(Releaser.objects.filter(name='Raww Arse').count(), 0)
        self.assertRedirects(response, '/groups/')

    def test_no_confirm(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.post('/releasers/%d/delete/' % self.gasman.id, {
            'no': 'no',
        })
        self.assertEqual(Releaser.objects.filter(name='Gasman').count(), 1)
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)


class TestEditExternalLinks(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')

    def test_locked(self):
        response = self.client.get('/releasers/%d/edit_external_links/' % self.papaya_dezign.id)
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        response = self.client.get('/releasers/%d/edit_external_links/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        sceneid_link = self.gasman.external_links.create(link_class='SceneidAccount', parameter='2260')
        pouet_link = self.gasman.external_links.create(link_class='PouetGroup', parameter='720')
        response = self.client.post('/releasers/%d/edit_external_links/' % self.gasman.id, {
            'external_links-TOTAL_FORMS': 3,
            'external_links-INITIAL_FORMS': 2,
            'external_links-MIN_NUM_FORMS': 0,
            'external_links-MAX_NUM_FORMS': 1000,
            'external_links-0-id': sceneid_link.id,
            'external_links-0-url': 'https://www.pouet.net/user.php?who=2260',
            'external_links-0-releaser': self.gasman.id,
            'external_links-0-DELETE': 'external_links-0-DELETE',
            'external_links-1-id': pouet_link.id,
            'external_links-1-url': 'https://www.pouet.net/groups.php?which=721',
            'external_links-1-releaser': self.gasman.id,
            'external_links-2-id': '',
            'external_links-2-url': 'https://twitter.com/gasmanic',
            'external_links-2-releaser': self.gasman.id,
        })
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(
            ReleaserExternalLink.objects.filter(releaser=self.gasman, link_class='SceneidAccount').count(),
            0
        )
        self.assertEqual(
            ReleaserExternalLink.objects.filter(releaser=self.gasman, link_class='PouetGroup').count(),
            1
        )
        self.assertEqual(
            ReleaserExternalLink.objects.filter(releaser=self.gasman, link_class='TwitterAccount').count(),
            1
        )

    def test_post_overlong(self):
        sceneid_link = self.gasman.external_links.create(link_class='SceneidAccount', parameter='2260')
        pouet_link = self.gasman.external_links.create(link_class='PouetGroup', parameter='720')
        response = self.client.post('/releasers/%d/edit_external_links/' % self.gasman.id, {
            'external_links-TOTAL_FORMS': 3,
            'external_links-INITIAL_FORMS': 2,
            'external_links-MIN_NUM_FORMS': 0,
            'external_links-MAX_NUM_FORMS': 1000,
            'external_links-0-id': sceneid_link.id,
            'external_links-0-url': 'https://www.pouet.net/user.php?who=2260',
            'external_links-0-releaser': self.gasman.id,
            'external_links-0-DELETE': 'external_links-0-DELETE',
            'external_links-1-id': pouet_link.id,
            'external_links-1-url': 'https://www.pouet.net/groups.php?which=721',
            'external_links-1-releaser': self.gasman.id,
            'external_links-2-id': '',
            'external_links-2-url': 'https://twitter.com/gasm' + ('a' * 10000) + 'nic',
            'external_links-2-releaser': self.gasman.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ensure this value has at most 4096 characters")

    def test_post_delete_multiple(self):
        sceneid_link = self.gasman.external_links.create(link_class='SceneidAccount', parameter='2260')
        pouet_link = self.gasman.external_links.create(link_class='PouetGroup', parameter='720')
        response = self.client.post('/releasers/%d/edit_external_links/' % self.gasman.id, {
            'external_links-TOTAL_FORMS': 3,
            'external_links-INITIAL_FORMS': 2,
            'external_links-MIN_NUM_FORMS': 0,
            'external_links-MAX_NUM_FORMS': 1000,
            'external_links-0-id': sceneid_link.id,
            'external_links-0-url': 'https://www.pouet.net/user.php?who=2260',
            'external_links-0-releaser': self.gasman.id,
            'external_links-0-DELETE': 'external_links-0-DELETE',
            'external_links-1-id': pouet_link.id,
            'external_links-1-url': 'https://www.pouet.net/groups.php?which=721',
            'external_links-1-releaser': self.gasman.id,
            'external_links-1-DELETE': 'external_links-1-DELETE',
            'external_links-2-id': '',
            'external_links-2-url': 'https://twitter.com/gasmanic',
            'external_links-2-releaser': self.gasman.id,
        })
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(
            ReleaserExternalLink.objects.filter(releaser=self.gasman, link_class='SceneidAccount').count(),
            0
        )
        self.assertEqual(
            ReleaserExternalLink.objects.filter(releaser=self.gasman, link_class='PouetGroup').count(),
            0
        )
        self.assertEqual(
            ReleaserExternalLink.objects.filter(releaser=self.gasman, link_class='TwitterAccount').count(),
            1
        )

    def test_post_update_multiple(self):
        sceneid_link = self.gasman.external_links.create(link_class='SceneidAccount', parameter='2250')
        pouet_link = self.gasman.external_links.create(link_class='PouetGroup', parameter='720')
        response = self.client.post('/releasers/%d/edit_external_links/' % self.gasman.id, {
            'external_links-TOTAL_FORMS': 3,
            'external_links-INITIAL_FORMS': 2,
            'external_links-MIN_NUM_FORMS': 0,
            'external_links-MAX_NUM_FORMS': 1000,
            'external_links-0-id': sceneid_link.id,
            'external_links-0-url': 'https://www.pouet.net/user.php?who=2260',
            'external_links-0-releaser': self.gasman.id,
            'external_links-1-id': pouet_link.id,
            'external_links-1-url': 'https://www.pouet.net/groups.php?which=721',
            'external_links-1-releaser': self.gasman.id,
            'external_links-2-id': '',
            'external_links-2-url': 'https://twitter.com/gasmanic',
            'external_links-2-releaser': self.gasman.id,
        })
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(
            ReleaserExternalLink.objects.filter(releaser=self.gasman, link_class='SceneidAccount').count(),
            1
        )
        self.assertEqual(
            ReleaserExternalLink.objects.filter(releaser=self.gasman, link_class='PouetGroup').count(),
            1
        )
        self.assertEqual(
            ReleaserExternalLink.objects.filter(releaser=self.gasman, link_class='TwitterAccount').count(),
            1
        )

    def test_post_nonunique(self):
        response = self.client.post('/releasers/%d/edit_external_links/' % self.gasman.id, {
            'external_links-TOTAL_FORMS': 2,
            'external_links-INITIAL_FORMS': 0,
            'external_links-MIN_NUM_FORMS': 0,
            'external_links-MAX_NUM_FORMS': 1000,
            'external_links-0-id': '',
            'external_links-0-url': 'https://twitter.com/gasmanic',
            'external_links-0-releaser': self.gasman.id,
            'external_links-1-id': '',
            'external_links-1-url': 'https://twitter.com/gasmanic',
            'external_links-1-releaser': self.gasman.id,
        })
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertEqual(
            ReleaserExternalLink.objects.filter(releaser=self.gasman, link_class='TwitterAccount').count(),
            1
        )


class TestLocking(TestCase):
    fixtures = ['tests/gasman.json']

    def setUp(self):
        User.objects.create_user(username='testuser', password='12345')
        User.objects.create_superuser(username='testsuperuser', email='testsuperuser@example.com', password='12345')
        self.gasman = Releaser.objects.get(name='Gasman')
        self.papaya_dezign = Releaser.objects.get(name='Papaya Dezign')

    def test_not_superuser(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/releasers/%d/lock/' % self.gasman.id)
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)

    def test_get_lock(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.get('/releasers/%d/lock/' % self.gasman.id)
        self.assertEqual(response.status_code, 200)

    def test_post_lock(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.post('/releasers/%d/lock/' % self.gasman.id, {
            'yes': 'yes'
        })
        self.assertRedirects(response, '/sceners/%d/' % self.gasman.id)
        self.assertTrue(Releaser.objects.get(name='Gasman').locked)

    def test_get_protected_view(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get('/releasers/%d/protected/' % self.papaya_dezign.id)
        self.assertEqual(response.status_code, 200)

    def test_post_unlock(self):
        self.client.login(username='testsuperuser', password='12345')
        response = self.client.post('/releasers/%d/protected/' % self.papaya_dezign.id, {
            'yes': 'yes'
        })
        self.assertRedirects(response, '/groups/%d/' % self.papaya_dezign.id)
        self.assertFalse(Releaser.objects.get(name='Papaya Dezign').locked)

    def test_non_superuser_cannot_unlock(self):
        self.client.login(username='testuser', password='12345')
        self.client.post('/releasers/%d/protected/' % self.papaya_dezign.id, {
            'yes': 'yes'
        })
        self.assertTrue(Releaser.objects.get(name='Papaya Dezign').locked)
