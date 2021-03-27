import unittest

from irctk.nick import Nick


class NickTests(unittest.TestCase):
    def setUp(self) -> None:
        self.nick = Nick('kylef', 'kyle', 'kylefuller.co.uk')

    def test_nick_initialization(self) -> None:
        self.assertEqual(self.nick.nick, 'kylef')
        self.assertEqual(self.nick.ident, 'kyle')
        self.assertEqual(self.nick.host, 'kylefuller.co.uk')

    def test_nick_parsing_from_userhost(self) -> None:
        nick = Nick.parse('kylef!kyle@kylefuller.co.uk')
        self.assertEqual(nick.nick, 'kylef')
        self.assertEqual(nick.ident, 'kyle')
        self.assertEqual(nick.host, 'kylefuller.co.uk')

    def test_nick_parsing_from_hostname(self) -> None:
        nick = Nick.parse('kylefuller.co.uk')
        self.assertEqual(nick.host, 'kylefuller.co.uk')

    def test_conversion_to_string(self) -> None:
        self.assertEqual(str(self.nick), 'kylef')

    def test_nick_repr(self) -> None:
        self.assertEqual(repr(self.nick), '<Nick kylef!kyle@kylefuller.co.uk>')
