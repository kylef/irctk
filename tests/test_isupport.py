import unittest

from irctk.isupport import ISupport


class ISupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.support = ISupport()

    # Defaults

    def test_default_maximum_nick_length(self) -> None:
        self.assertEqual(self.support.maximum_nick_length, 9)

    def test_default_maximum_channel_length(self) -> None:
        self.assertEqual(self.support.maximum_channel_length, 200)

    def test_default_channel_prefixes(self) -> None:
        self.assertEqual(self.support.channel_prefixes, ['#', '&'])

    def test_default_user_channel_modes(self) -> None:
        self.assertEqual(self.support['prefix'], {'o': '@', 'v': '+'})

    def test_default_case_mapping(self) -> None:
        self.assertEqual(self.support.case_mapping, 'rfc1459')

    # Is channel

    def test_is_channel_disallows_commas(self) -> None:
        self.assertFalse(self.support.is_channel('#te,st'))

    def test_is_channel_disallows_spaces(self) -> None:
        self.assertFalse(self.support.is_channel('#te st'))

    def test_is_channel_allows_channels_with_channel_prefix(self) -> None:
        self.support['chantypes'] = ['$']
        self.assertTrue(self.support.is_channel('$test'))

    def test_is_channel_disallows_chanels_without_channel_prefix(self) -> None:
        self.assertFalse(self.support.is_channel('$test'))

    def test_is_channel_disallows_channels_exceeding_maximum_length(self) -> None:
        self.support['channellen'] = 5
        self.assertFalse(self.support.is_channel('#testing'))

    # Test parsing

    def test_can_parse_nicklen(self) -> None:
        self.support.parse('NICKLEN=5')
        self.assertEqual(self.support.maximum_nick_length, 5)

    def test_can_parse_channellen(self) -> None:
        self.support.parse('CHANNELLEN=10')
        self.assertEqual(self.support.maximum_channel_length, 10)

    def test_can_parse_prefix(self) -> None:
        self.support.parse('PREFIX=(ohv)$%+')
        self.assertEqual(self.support['prefix'], {'o': '$', 'h': '%', 'v': '+'})

    def test_can_parse_chanmodes(self) -> None:
        self.support.parse('CHANMODES=ae,bf,cg,dh')
        self.assertEqual(
            self.support['chanmodes'],
            {
                'a': list,
                'e': list,
                'b': 'arg',
                'f': 'arg',
                'c': 'arg_set',
                'g': 'arg_set',
                'd': None,
                'h': None,
            },
        )

    def test_can_parse_chantypes(self) -> None:
        self.support.parse('CHANTYPES=$^')
        self.assertEqual(self.support['chantypes'], ['$', '^'])

    def test_can_parse_removal(self) -> None:
        self.support.parse('MONITOR')
        assert 'MONITOR' in self.support

        self.support.parse('-MONITOR')
        assert 'MONITOR' not in self.support

    def test_can_parse_removal_reverts_to_default(self) -> None:
        self.support.parse('CASEMAPPING=ascii')
        assert self.support.case_mapping == 'ascii'

        self.support.parse('-CASEMAPPING')
        assert self.support.case_mapping == 'rfc1459'

    # Test construction

    def test_can_be_converted_to_string(self) -> None:
        line = str(self.support)

        new_support = ISupport()
        new_support.clear()
        new_support.parse(line)

        self.assertEqual(new_support, self.support)
