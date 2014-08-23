import unittest
from irctk.client import Client


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.client = Client('kylef', 'kyle', 'Kyle Fuller')
        self.sent_lines = []

        def send_line(line):
            self.sent_lines.append(line)

        self.client.send_line = send_line

    def test_client_has_nickname(self):
        self.assertEqual(self.client.nickname, 'kylef')

    def test_client_has_ident(self):
        self.assertEqual(self.client.ident, 'kyle')

    def test_client_has_realname(self):
        self.assertEqual(self.client.realname, 'Kyle Fuller')

    # Registration

    def test_client_is_not_registered_by_default(self):
        self.assertFalse(self.client.is_registered)

    def test_client_is_registered_after_001(self):
        self.client.read_data(':irc.kylefuller.co.uk 001 kyle :Welcome')
        self.assertTrue(self.client.is_registered)

    # Ping

    def test_client_sends_pong_when_pinged(self):
        self.client.read_data('PING :hello')
        self.assertEqual(self.sent_lines, ['PONG hello'])

