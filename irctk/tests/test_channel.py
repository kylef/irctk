import unittest
from irctk.channel import Channel
from irctk.tests.mock_client import MockClient as Client


class ChannelTests(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.channel = Channel(self.client, '#testing')

    def test_channel_has_name(self):
        self.assertEqual(self.channel.name, '#testing')

    def test_channel_convertable_to_string(self):
        self.assertEqual(str(self.channel), '#testing')

    def test_channel_repr(self):
        self.assertEqual(repr(self.channel), '<Channel #testing>')

    def test_send_message_to_channel(self):
        self.channel.send('Hello World')
        self.assertEqual(self.client.sent_lines, ['PRIVMSG #testing :Hello World'])

    def test_parting_sends_part(self):
        self.channel.part()
        self.assertEqual(self.client.sent_lines, ['PART #testing'])

