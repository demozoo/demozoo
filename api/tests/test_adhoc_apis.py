from __future__ import absolute_import, unicode_literals

import json

from django.test import TestCase

from demoscene.models import Releaser, ReleaserExternalLink
from parties.models import Party, PartyExternalLink
from productions.models import Production, ProductionLink, ProductionType


class TestPouet(TestCase):
	fixtures = ['tests/gasman.json']

	def setUp(self):
		pondlife = Production.objects.get(title='Pondlife')
		ProductionLink.objects.create(
			production=pondlife, link_class='PouetProduction', parameter='2611', is_download_link=False
		)
		gasman = Releaser.objects.get(name='Gasman')
		ReleaserExternalLink.objects.create(
			releaser=gasman, link_class='SceneidAccount', parameter='2260'
		)
		raww_arse = Releaser.objects.get(name='Raww Arse')
		ReleaserExternalLink.objects.create(
			releaser=raww_arse, link_class='PouetGroup', parameter='123'
		)
		forever2e3 = Party.objects.get(name='Forever 2e3')
		PartyExternalLink.objects.create(
			party=forever2e3, link_class='PouetParty', parameter='181/2000'
		)

	def test_pouet_credits(self):
		response = self.client.get('/api/adhoc/pouet-credits/')
		self.assertEqual(response.status_code, 200)

		response_data = json.loads(response.content)
		results = [
			result
			for result in response_data
			if result['pouet_user_id'] == '2260' and result['pouet_prod_id'] == '2611'
		]
		self.assertEqual(results[0]['role'], "Code")

	def test_prod_demozoo_ids(self):
		response = self.client.get('/api/adhoc/pouet/prod-demozoo-ids-by-pouet-id/')
		self.assertEqual(response.status_code, 200)

		response_data = json.loads(response.content)
		results = [
			result
			for result in response_data
			if result['demozoo_id'] == 4 and result['pouet_id'] == 2611
		]
		self.assertEqual(1, len(results))

	def test_group_demozoo_ids(self):
		response = self.client.get('/api/adhoc/pouet/group-demozoo-ids-by-pouet-id/')
		self.assertEqual(response.status_code, 200)
		response_data = json.loads(response.content)
		results = [
			result
			for result in response_data
			if result['demozoo_id'] == 2 and result['pouet_id'] == 123
		]
		self.assertEqual(1, len(results))

	def test_party_demozoo_ids(self):
		response = self.client.get('/api/adhoc/pouet/party-demozoo-ids-by-pouet-id/')
		self.assertEqual(response.status_code, 200)

		response_data = json.loads(response.content)
		results = [
			result
			for result in response_data
			if result['demozoo_id'] == 1 and result['pouet_id'] == 181 and result['year'] == 2000
		]
		self.assertEqual(1, len(results))


class TestZxdemo(TestCase):
	fixtures = ['tests/gasman.json']

	def setUp(self):
		pondlife = Production.objects.get(title='Pondlife')
		ProductionLink.objects.create(
			production=pondlife, link_class='ZxdemoItem', parameter='3130', is_download_link=False
		)
		raww_arse = Releaser.objects.get(name='Raww Arse')
		ReleaserExternalLink.objects.create(
			releaser=raww_arse, link_class='ZxdemoAuthor', parameter='404'
		)
		forever2e3 = Party.objects.get(name='Forever 2e3')
		PartyExternalLink.objects.create(
			party=forever2e3, link_class='ZxdemoParty', parameter='16'
		)

	def test_prod_demozoo_ids(self):
		response = self.client.get('/api/adhoc/zxdemo/prod-demozoo-ids-by-zxdemo-id/')
		self.assertEqual(response.status_code, 200)

		response_data = json.loads(response.content)
		results = [
			result
			for result in response_data
			if result['demozoo_id'] == 4 and result['zxdemo_id'] == 3130
		]
		self.assertEqual(1, len(results))

	def test_group_demozoo_ids(self):
		response = self.client.get('/api/adhoc/zxdemo/group-demozoo-ids-by-zxdemo-id/')
		self.assertEqual(response.status_code, 200)
		response_data = json.loads(response.content)
		results = [
			result
			for result in response_data
			if result['demozoo_id'] == 2 and result['zxdemo_id'] == 404
		]
		self.assertEqual(1, len(results))

	def test_party_demozoo_ids(self):
		response = self.client.get('/api/adhoc/zxdemo/party-demozoo-ids-by-zxdemo-id/')
		self.assertEqual(response.status_code, 200)

		response_data = json.loads(response.content)
		results = [
			result
			for result in response_data
			if result['demozoo_id'] == 1 and result['zxdemo_id'] == 16
		]
		self.assertEqual(1, len(results))


class TestEq(TestCase):
	fixtures = ['tests/gasman.json']

	def test_eq_prods(self):
		response = self.client.get('/api/adhoc/eq/demos/')
		self.assertEqual(response.status_code, 200)
		self.assertIn("Madrielle", response.content)


class TestKlubi(TestCase):
	fixtures = ['tests/gasman.json']

	def setUp(self):
		game = ProductionType.add_root(name='Game')
		stevie_dotman = Production.objects.create(
			title="Stevie Dotman", supertype="production",
			release_date_date='2000-03-18', release_date_precision='d'
		)
		stevie_dotman.types.add(game)

		Production.objects.create(
			title="Mystery Prod", supertype="production",
			release_date_date='2000-03-18', release_date_precision='d'
		)

	def test_klubi_demoshow(self):
		response = self.client.get('/api/adhoc/klubi/demoshow-prods/')
		self.assertEqual(response.status_code, 200)
		self.assertIn("Demozoo URL,Title,By,Release date,Party", response.content)

	def test_klubi_demoshow_for_specific_month(self):
		response = self.client.get('/api/adhoc/klubi/demoshow-prods/?month=2000-03')
		self.assertEqual(response.status_code, 200)
		self.assertIn("Madrielle", response.content)
		# don't include games
		self.assertNotIn("Stevie Dotman", response.content)
		# do include prods with no type listed
		self.assertIn("Mystery Prod", response.content)


class TestScenesat(TestCase):
	fixtures = ['tests/gasman.json']

	def setUp(self):
		Production.objects.create(
			title="Cybernoid's Revenge", supertype="music",
			release_date_date='2001-03-18', release_date_precision='d'
		)

	def test_scenesat_releases(self):
		response = self.client.get('/api/adhoc/scenesat/monthly-releases/')
		self.assertEqual(response.status_code, 200)
		self.assertIn("Demozoo URL,Title,By,Release date", response.content)

	def test_scenesat_releases_for_specific_month(self):
		response = self.client.get('/api/adhoc/scenesat/monthly-releases/?month=2001-03')
		self.assertEqual(response.status_code, 200)
		self.assertIn("Cybernoid's Revenge", response.content)
