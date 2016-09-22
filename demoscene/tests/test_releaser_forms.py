from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from demoscene.forms.releaser import (
	CreateGroupForm, CreateScenerForm, ScenerEditLocationForm, ScenerEditRealNameForm
)
from demoscene.models import Releaser, Edit


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
