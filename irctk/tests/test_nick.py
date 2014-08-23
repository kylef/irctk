import unittest
from irctk.nick import Nick
from irctk.tests.mock_client import MockClient as Client


class NickTests(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.nick = Nick(self.client, 'kylef', 'kyle', 'kylefuller.co.uk')

    def test_nick_initialization(self):
        self.assertEqual(self.nick.nick, 'kylef')
        self.assertEqual(self.nick.ident, 'kyle')
        self.assertEqual(self.nick.host, 'kylefuller.co.uk')

    def test_nick_parsing_from_userhost(self):
        nick = Nick.parse(self.client, 'kylef!kyle@kylefuller.co.uk')
        self.assertEqual(nick.nick, 'kylef')
        self.assertEqual(nick.ident, 'kyle')
        self.assertEqual(nick.host, 'kylefuller.co.uk')

    def test_nick_parsing_from_hostname(self):
        nick = Nick.parse(self.client, 'kylefuller.co.uk')
        self.assertEqual(nick.host, 'kylefuller.co.uk')

    def test_conversion_to_string(self):
        self.assertEqual(str(self.nick), 'kylef')

    def test_nick_repr(self):
        self.assertEqual(repr(self.nick), '<Nick kylef!kyle@kylefuller.co.uk>')

    #

    def test_send_message_to_nick(self):
        self.nick.send('Hello World')
        self.assertEqual(self.client.sent_lines, ['PRIVMSG kylef :Hello World'])

