import unittest
from irctk.isupport import ISupport

class ISupportTests(unittest.TestCase):
    def setUp(self):
        self.support = ISupport()

    # Defaults

    def test_default_maximum_nick_length(self):
        self.assertEqual(self.support.maximum_nick_length, 9)

    def test_default_maximum_channel_length(self):
        self.assertEqual(self.support.maximum_channel_length, 200)

    def test_default_channel_prefixes(self):
        self.assertEqual(self.support.channel_prefixes, ['#', '&'])

    def test_default_user_channel_modes(self):
        self.assertEqual(self.support['prefix'], {'o': '@', 'v': '+'})

