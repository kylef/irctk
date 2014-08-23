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

    # Is channel

    def test_is_channel_disallows_commas(self):
        self.assertFalse(self.support.is_channel('#te,st'))

    def test_is_channel_disallows_spaces(self):
        self.assertFalse(self.support.is_channel('#te st'))

    def test_is_channel_allows_channels_with_channel_prefix(self):
        self.support['chantypes'] = ['$']
        self.assertTrue(self.support.is_channel('$test'))

    def test_is_channel_disallows_chanels_without_channel_prefix(self):
        self.assertFalse(self.support.is_channel('$test'))

    def test_is_channel_disallows_channels_exceeding_maximum_length(self):
        self.support['channellen'] = 5
        self.assertFalse(self.support.is_channel('#testing'))

    # Test parsing

    def test_can_parse_nicklen(self):
        self.support.parse('NICKLEN=5')
        self.assertEqual(self.support.maximum_nick_length, 5)

    def test_can_parse_channellen(self):
        self.support.parse('CHANNELLEN=10')
        self.assertEqual(self.support.maximum_channel_length, 10)

    def test_can_parse_prefix(self):
        self.support.parse('PREFIX=(ohv)$%+')
        self.assertEqual(self.support['prefix'], {'o': '$', 'h': '%', 'v': '+'})

