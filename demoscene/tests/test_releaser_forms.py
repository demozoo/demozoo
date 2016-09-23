from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from demoscene.forms.releaser import (
	CreateGroupForm, CreateScenerForm, ScenerEditLocationForm, ScenerEditRealNameForm,
	ReleaserEditNotesForm, ScenerNickForm, GroupNickForm
)
from demoscene.models import Releaser, Edit, Nick


class TestCreateGroupForm(TestCase):
	def setUp(self):
		self.user = User.objects.create_user('bob')

	def test_create(self):
		form = CreateGroupForm({
			'name': 'Poo-Brain',
			'abbreviation': 'PB',
			'nick_variant_list': 'Poo Brain, PooBrain'
		})
		self.assertTrue(form.is_valid())
		form.save()

		releaser = Releaser.objects.get(name='Poo-Brain')
		self.assertTrue(releaser.abbreviation, 'PB')
		self.assertTrue(releaser.is_group)

		self.assertEqual(releaser.primary_nick.name, 'Poo-Brain')

		nick_variants = [variant.name for variant in releaser.primary_nick.variants.all()]
		self.assertIn('Poo-Brain', nick_variants)
		self.assertIn('Poo Brain', nick_variants)
		self.assertIn('PooBrain', nick_variants)

		form.log_creation(self.user)
		log_entry = Edit.objects.get(
			action_type='create_group',
			focus_content_type=ContentType.objects.get_for_model(Releaser),
			focus_object_id=releaser.id
		)
		self.assertEqual(log_entry.user, self.user)


class TestCreateScenerForm(TestCase):
	def setUp(self):
		self.user = User.objects.create_user('bob')

	def test_create(self):
		form = CreateScenerForm({
			'name': 'Factor6',
			'nick_variant_list': 'Factor 6, F6'
		})
		self.assertTrue(form.is_valid())
		form.save()

		releaser = Releaser.objects.get(name='Factor6')
		self.assertFalse(releaser.is_group)

		self.assertEqual(releaser.primary_nick.name, 'Factor6')

		nick_variants = [variant.name for variant in releaser.primary_nick.variants.all()]
		self.assertIn('Factor6', nick_variants)
		self.assertIn('Factor 6', nick_variants)
		self.assertIn('F6', nick_variants)

		form.log_creation(self.user)
		log_entry = Edit.objects.get(
			action_type='create_scener',
			focus_content_type=ContentType.objects.get_for_model(Releaser),
			focus_object_id=releaser.id
		)
		self.assertEqual(log_entry.user, self.user)


class TestScenerEditLocationForm(TestCase):
	def setUp(self):
		self.scener = Releaser.objects.create(
			name='Gasman',
			location='Adlington, Lancashire, England, United Kingdom',
			latitude=53.61323,
			longitude=-2.60676,
			country_code='GB',
			geonames_id=2657668,
			is_group=False,
		)
		self.user = User.objects.create_user('bob')

	def test_edit(self):
		form = ScenerEditLocationForm({
			'location': 'Oxford'
		}, instance=self.scener)
		self.assertTrue(form.is_valid())
		form.save()

		self.assertEqual(self.scener.location, 'Oxford, Oxfordshire, England, United Kingdom')
		self.assertEqual(self.scener.country_code, 'GB')
		self.assertEqual(self.scener.latitude, 51.75222)
		self.assertEqual(self.scener.longitude, -1.25596)
		self.assertEqual(self.scener.geonames_id, 2640729)

		form.log_edit(self.user)
		log_entry = Edit.objects.get(
			action_type='edit_scener_location',
			focus_content_type=ContentType.objects.get_for_model(Releaser),
			focus_object_id=self.scener.id
		)
		self.assertEqual(log_entry.user, self.user)
		self.assertEqual(log_entry.description, "Set location to Oxford, Oxfordshire, England, United Kingdom")

	def test_unset(self):
		form = ScenerEditLocationForm({
			'location': ''
		}, instance=self.scener)
		self.assertTrue(form.is_valid())
		form.save()

		self.assertEqual(self.scener.location, '')
		self.assertEqual(self.scener.country_code, '')
		self.assertEqual(self.scener.latitude, None)
		self.assertEqual(self.scener.longitude, None)
		self.assertEqual(self.scener.geonames_id, None)

	def test_leave_unchanged(self):
		# Must not perform a location lookup, as location is unchanged
		form = ScenerEditLocationForm({
			'location': 'Adlington, Lancashire, England, United Kingdom'
		}, instance=self.scener)
		self.assertTrue(form.is_valid())
		form.save()

		self.assertEqual(self.scener.location, 'Adlington, Lancashire, England, United Kingdom')

	def test_unrecognised_location(self):
		form = ScenerEditLocationForm({
			'location': 'Royston Vasey'
		}, instance=self.scener)
		self.assertFalse(form.is_valid())
		self.assertEqual(form.errors['location'], ["Location not recognised"])


class TestScenerEditRealNameForm(TestCase):
	def setUp(self):
		self.scener = Releaser.objects.create(
			name='Gasman',
			first_name='Matt', surname='Westcott',
			show_first_name=True, show_surname=True,
			is_group=False,
		)
		self.user = User.objects.create_user('bob')

	def test_edit(self):
		form = ScenerEditRealNameForm({
			'first_name': 'Matt', 'surname': 'Westcottski',
			'show_first_name': 'true',
			'real_name_note': "he's feeling a bit shy",
		}, instance=self.scener)
		self.assertTrue(form.is_valid())
		form.save()
		self.assertEqual(self.scener.surname, 'Westcottski')
		self.assertFalse(self.scener.show_surname)

		form.log_edit(self.user)
		log_entry = Edit.objects.get(
			action_type='edit_scener_real_name',
			focus_content_type=ContentType.objects.get_for_model(Releaser),
			focus_object_id=self.scener.id
		)
		self.assertEqual(log_entry.user, self.user)
		self.assertEqual(log_entry.description, "Set real name")

	def test_log_message_when_name_unchanged(self):
		form = ScenerEditRealNameForm({
			'first_name': 'Matt', 'surname': 'Westcott',
			'show_first_name': 'true',
			'real_name_note': "he's feeling a bit shy",
		}, instance=self.scener)
		self.assertTrue(form.is_valid())
		form.save()
		self.assertEqual(self.scener.surname, 'Westcott')
		self.assertFalse(self.scener.show_surname)

		form.log_edit(self.user)
		log_entry = Edit.objects.get(
			action_type='edit_scener_real_name',
			focus_content_type=ContentType.objects.get_for_model(Releaser),
			focus_object_id=self.scener.id
		)
		self.assertEqual(log_entry.user, self.user)
		self.assertEqual(log_entry.description, "Updated visibility of real name")

	def test_no_log_message_when_no_change(self):
		form = ScenerEditRealNameForm({
			'first_name': 'Matt', 'surname': 'Westcott',
			'show_first_name': 'true', 'show_surname': 'true',
			'real_name_note': "",
		}, instance=self.scener)
		self.assertTrue(form.is_valid())
		form.save()
		self.assertEqual(self.scener.surname, 'Westcott')
		self.assertTrue(self.scener.show_surname)

		form.log_edit(self.user)
		log_entry = Edit.objects.filter(
			action_type='edit_scener_real_name',
			focus_content_type=ContentType.objects.get_for_model(Releaser),
			focus_object_id=self.scener.id
		)
		self.assertFalse(log_entry)


class TestReleaserEditNotesForm(TestCase):
	def setUp(self):
		self.scener = Releaser.objects.create(
			name='Gasman',
			notes="it me",
			is_group=False,
		)
		self.user = User.objects.create_user('bob')

	def test_edit(self):
		form = ReleaserEditNotesForm({
			'notes': "it still me"
		}, instance=self.scener)
		self.assertTrue(form.is_valid())
		form.save()
		self.assertEqual(self.scener.notes, "it still me")
		form.log_edit(self.user)

		log_entry = Edit.objects.get(
			action_type='edit_releaser_notes',
			focus_content_type=ContentType.objects.get_for_model(Releaser),
			focus_object_id=self.scener.id
		)
		self.assertEqual(log_entry.user, self.user)
		self.assertEqual(log_entry.description, "Edited notes")


class TestScenerNickForm(TestCase):
	def setUp(self):
		self.scener = Releaser.objects.create(name='Gasman', is_group=False)
		self.primary_nick = self.scener.primary_nick
		self.secondary_nick = Nick.objects.create(releaser=self.scener, name='Shingebis')
		self.user = User.objects.create_user('bob')

	def test_render_add(self):
		form = ScenerNickForm(self.scener)
		html = form.as_p()

		# the 'add nick' form gives the option to set preferred name
		self.assertIn("Use this as their preferred name, instead of &#39;Gasman&#39;", html)

		# scener nicks never get differentiators or abbreviations
		self.assertNotIn("Differentiator", html)
		self.assertNotIn("Abbreviation", html)

	def test_render_add_for_admin(self):
		form = ScenerNickForm(self.scener, for_admin=True)
		html = form.as_p()

		# the 'add nick' form gives the option to set preferred name
		self.assertIn("Use this as their preferred name, instead of &#39;Gasman&#39;", html)

		# scener nicks never get differentiators or abbreviations
		self.assertNotIn("Differentiator", html)
		self.assertNotIn("Abbreviation", html)

	def test_render_edit_primary(self):
		form = ScenerNickForm(self.scener, instance=self.primary_nick)
		html = form.as_p()

		# No 'preferred name' checkbox, as this is already the primary nick
		self.assertNotIn("Use this as their preferred name, instead of &#39;Gasman&#39;", html)

		# scener nicks never get differentiators or abbreviations
		self.assertNotIn("Differentiator", html)
		self.assertNotIn("Abbreviation", html)

	def test_render_edit_primary_for_admin(self):
		form = ScenerNickForm(self.scener, instance=self.primary_nick, for_admin=True)
		html = form.as_p()

		# No 'preferred name' checkbox, as this is already the primary nick
		self.assertNotIn("Use this as their preferred name, instead of &#39;Gasman&#39;", html)

		# scener nicks never get differentiators or abbreviations
		self.assertNotIn("Differentiator", html)
		self.assertNotIn("Abbreviation", html)

	def test_render_edit_secondary(self):
		form = ScenerNickForm(self.scener, instance=self.secondary_nick)
		html = form.as_p()

		# show 'preferred name' checkbox
		self.assertIn("Use this as their preferred name, instead of &#39;Gasman&#39;", html)

		# scener nicks never get differentiators or abbreviations
		self.assertNotIn("Differentiator", html)
		self.assertNotIn("Abbreviation", html)

	def test_render_edit_secondary_for_admin(self):
		form = ScenerNickForm(self.scener, instance=self.secondary_nick, for_admin=True)
		html = form.as_p()

		# show 'preferred name' checkbox
		self.assertIn("Use this as their preferred name, instead of &#39;Gasman&#39;", html)

		# scener nicks never get differentiators or abbreviations
		self.assertNotIn("Differentiator", html)
		self.assertNotIn("Abbreviation", html)

	def test_add_nick(self):
		nick = Nick(releaser=self.scener)
		form = ScenerNickForm(
			self.scener, {'name': 'Dj.Mo0nbug', 'nick_variant_list': 'moonbug, mo0nbug'},
			instance=nick
		)
		self.assertTrue(form.is_valid())
		form.save()
		saved_nick = self.scener.nicks.get(name='Dj.Mo0nbug')
		self.assertTrue(saved_nick.variants.filter(name='mo0nbug').exists())

		form.log_creation(self.user)
		log_entry = Edit.objects.get(
			action_type='add_nick',
			focus_content_type=ContentType.objects.get_for_model(Releaser),
			focus_object_id=self.scener.id
		)
		self.assertEqual(log_entry.user, self.user)
		self.assertEqual(log_entry.description, "Added nick 'Dj.Mo0nbug'")

	def test_reject_add_duplicate_nick(self):
		nick = Nick(releaser=self.scener)
		form = ScenerNickForm(
			self.scener, {'name': 'Shingebis', 'nick_variant_list': ''},
			instance=nick
		)
		self.assertFalse(form.is_valid())
		self.assertEqual(form.errors['__all__'], ["This nick cannot be added, as it duplicates an existing one."])

	def test_can_duplicate_other_scener_nick_on_add(self):
		"""
		The duplicate nick check is only enforced for nicks belonging to the same releaser;
		a scener CAN have the same nick as someone else
		"""
		Releaser.objects.create(name='Spartacus', is_group=False)

		nick = Nick(releaser=self.scener)
		form = ScenerNickForm(
			self.scener, {'name': 'Spartacus', 'nick_variant_list': ''},
			instance=nick
		)
		self.assertTrue(form.is_valid())

	def test_edit_nick(self):
		form = ScenerNickForm(
			self.scener,
			{'name': 'Shingebiscuit', 'nick_variant_list': 'Shingebourbon', 'override_primary_nick': 'true'},
			instance=self.secondary_nick
		)
		self.assertTrue(form.is_valid())
		form.save()
		saved_nick = self.scener.nicks.get(name='Shingebiscuit')
		self.assertTrue(saved_nick.variants.filter(name='Shingebourbon').exists())
		self.assertFalse(self.scener.nicks.filter(name='Shingebis').exists())

		form.log_edit(self.user)
		log_entry = Edit.objects.get(
			action_type='edit_nick',
			focus_content_type=ContentType.objects.get_for_model(Releaser),
			focus_object_id=self.scener.id
		)
		self.assertEqual(log_entry.user, self.user)
		self.assertEqual(
			log_entry.description,
			"Edited nick 'Shingebiscuit': changed name to 'Shingebiscuit'; changed aliases to 'Shingebourbon'; set as primary nick"
		)

	def test_reject_edit_duplicate_nick(self):
		form = ScenerNickForm(
			self.scener, {'name': 'Gasman', 'nick_variant_list': ''},
			instance=self.secondary_nick
		)
		self.assertFalse(form.is_valid())
		self.assertEqual(form.errors['__all__'], ["This nick cannot be added, as it duplicates an existing one."])

	def test_edit_nick_without_changing_name(self):
		form = ScenerNickForm(
			self.scener, {'name': 'Shingebis', 'nick_variant_list': 'Shingebourbon'},
			instance=self.secondary_nick
		)
		self.assertTrue(form.is_valid())
		form.save()

		form.log_edit(self.user)
		log_entry = Edit.objects.get(
			action_type='edit_nick',
			focus_content_type=ContentType.objects.get_for_model(Releaser),
			focus_object_id=self.scener.id
		)
		self.assertEqual(log_entry.user, self.user)
		self.assertEqual(
			log_entry.description,
			"Edited nick 'Shingebis': changed aliases to 'Shingebourbon'"
		)

	def test_can_duplicate_other_scener_nick_on_edit(self):
		"""
		The duplicate nick check is only enforced for nicks belonging to the same releaser;
		a scener CAN have the same nick as someone else
		"""
		Releaser.objects.create(name='Spartacus', is_group=False)

		form = ScenerNickForm(
			self.scener, {'name': 'Spartacus', 'nick_variant_list': ''},
			instance=self.secondary_nick
		)
		self.assertTrue(form.is_valid())


class TestGroupNickForm(TestCase):
	def setUp(self):
		self.group = Releaser.objects.create(name='Placebo', is_group=True)
		self.primary_nick = self.group.primary_nick
		self.secondary_nick = Nick.objects.create(releaser=self.group, name='Eternity Industry')
		self.user = User.objects.create_user('bob')

	def test_render_add(self):
		form = GroupNickForm(self.group)
		html = form.as_p()

		# the 'add nick' form gives the option to set preferred name
		self.assertIn("Use this as their preferred name, instead of &#39;Placebo&#39;", html)

		# group nicks can have abbreviations
		self.assertIn("Abbreviation", html)
		# differentiator field is only available to admins
		self.assertNotIn("Differentiator", html)

	def test_render_add_for_admin(self):
		form = GroupNickForm(self.group, for_admin=True)
		html = form.as_p()

		# the 'add nick' form gives the option to set preferred name
		self.assertIn("Use this as their preferred name, instead of &#39;Placebo&#39;", html)

		# group nicks can have abbreviations
		self.assertIn("Abbreviation", html)
		# differentiator field is available to admins
		self.assertIn("Differentiator", html)

	def test_render_edit_primary(self):
		form = GroupNickForm(self.group, instance=self.primary_nick)
		html = form.as_p()

		# No 'preferred name' checkbox, as this is already the primary nick
		self.assertNotIn("Use this as their preferred name, instead of &#39;Placebo&#39;", html)

		# group nicks can have abbreviations
		self.assertIn("Abbreviation", html)
		# differentiator field is only available to admins
		self.assertNotIn("Differentiator", html)

	def test_render_edit_primary_for_admin(self):
		form = GroupNickForm(self.group, instance=self.primary_nick, for_admin=True)
		html = form.as_p()

		# No 'preferred name' checkbox, as this is already the primary nick
		self.assertNotIn("Use this as their preferred name, instead of &#39;Gasman&#39;", html)

		# group nicks can have abbreviations
		self.assertIn("Abbreviation", html)
		# differentiator field is available to admins
		self.assertIn("Differentiator", html)

	def test_render_edit_secondary(self):
		form = GroupNickForm(self.group, instance=self.secondary_nick)
		html = form.as_p()

		# show 'preferred name' checkbox
		self.assertIn("Use this as their preferred name, instead of &#39;Placebo&#39;", html)

		# group nicks can have abbreviations
		self.assertIn("Abbreviation", html)
		# differentiator field is only available to admins
		self.assertNotIn("Differentiator", html)

	def test_render_edit_secondary_for_admin(self):
		form = GroupNickForm(self.group, instance=self.secondary_nick, for_admin=True)
		html = form.as_p()

		# show 'preferred name' checkbox
		self.assertIn("Use this as their preferred name, instead of &#39;Placebo&#39;", html)

		# group nicks can have abbreviations
		self.assertIn("Abbreviation", html)
		# differentiator field is available to admins
		self.assertIn("Differentiator", html)

	def test_edit_nick(self):
		form = GroupNickForm(
			self.group,
			{
				'name': 'Obecalp', 'abbreviation': 'BCP', 'differentiator': 'ZX',
				'nick_variant_list': 'Ob3calp', 'override_primary_nick': 'true'
			},
			instance=self.secondary_nick,
			for_admin=True
		)
		self.assertTrue(form.is_valid())
		form.save()
		saved_nick = self.group.nicks.get(name='Obecalp')
		self.assertTrue(saved_nick.variants.filter(name='Ob3calp').exists())
		self.assertFalse(self.group.nicks.filter(name='Eternity Industry').exists())

		form.log_edit(self.user)
		log_entry = Edit.objects.get(
			action_type='edit_nick',
			focus_content_type=ContentType.objects.get_for_model(Releaser),
			focus_object_id=self.group.id
		)
		self.assertEqual(log_entry.user, self.user)
		self.assertEqual(
			log_entry.description,
			"Edited nick 'Obecalp': changed name to 'Obecalp'; changed abbreviation to 'BCP'; changed differentiator to 'ZX'; changed aliases to 'Ob3calp'; set as primary nick"
		)
