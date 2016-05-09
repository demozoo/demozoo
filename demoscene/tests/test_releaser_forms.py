from __future__ import absolute_import, unicode_literals

import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from demoscene.forms.releaser import CreateGroupForm, CreateScenerForm
from demoscene.models import Releaser, Edit


class TestCreateGroupForm(TestCase):
	def setUp(self):
		self.user = User.objects.create_user('bob')

	def test_create(self):
		group = Releaser(is_group=True, updated_at=datetime.datetime.now())  # FIXME: the form should handle this
		form = CreateGroupForm({
			'name': 'Poo-Brain',
			'abbreviation': 'PB',
			'nick_variant_list': 'Poo Brain, PooBrain'
		}, instance=group)
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
		scener = Releaser(is_group=False, updated_at=datetime.datetime.now())  # FIXME: the form should handle this
		form = CreateScenerForm({
			'name': 'Factor6',
			'nick_variant_list': 'Factor 6, F6'
		}, instance=scener)
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
