from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from demoscene.utils.nick_search import NickSelection


class TestNickSelection(TestCase):
    def test_str(self):
        ns = NickSelection(123, 'Gasman')
        self.assertEqual(str(ns), 'Gasman')

    def test_repr(self):
        ns = NickSelection(123, 'Gasman')
        self.assertEqual(repr(ns), 'NickSelection: 123, Gasman')

    def test_eq(self):
        self.assertTrue(NickSelection('newscener', 'Gasman') == NickSelection('newscener', 'Gasman'))
        self.assertTrue(NickSelection('newgroup', 'Fairlight') == NickSelection('newgroup', 'Fairlight'))
        self.assertFalse(NickSelection(123, 'Gasman') == NickSelection('newscener', 'Gasman'))
        self.assertFalse(NickSelection('newscener', 'Equinox') == NickSelection('newgroup', 'Equinox'))

    def test_neq(self):
        self.assertTrue(NickSelection(123, 'Gasman') != NickSelection(124, 'Gasman'))
        self.assertFalse(NickSelection(123, 'Raww Arse') != NickSelection(123, 'RA'))
