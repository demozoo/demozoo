# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from platforms.models import Platform
from productions.models import Production, ProductionType


class TestProductionType(TestCase):
    fixtures = ['tests/gasman.json']

    def test_music_types(self):
        ProductionType.objects.filter(internal_name='music').delete()
        self.assertEqual(ProductionType.music_types().count(), 0)

    def test_graphic_types(self):
        ProductionType.objects.filter(internal_name='graphics').delete()
        self.assertEqual(ProductionType.graphic_types().count(), 0)


class TestProduction(TestCase):
    fixtures = ['tests/gasman.json']

    def test_title_with_byline(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.author_nicks.clear()
        pondlife.author_affiliation_nicks.clear()
        self.assertEqual(pondlife.title_with_byline, 'Pondlife')

    def test_multiple_platform_name(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.platforms.add(Platform.objects.get(name='Commodore 64'))
        self.assertEqual(pondlife.platform_name, '(multiple)')

    def test_multiple_type_name(self):
        pondlife = Production.objects.get(title='Pondlife')
        pondlife.types.add(ProductionType.objects.get(name='Intro'))
        self.assertEqual(pondlife.type_name, '(multiple)')
