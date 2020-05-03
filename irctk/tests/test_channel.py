import unittest
from irctk.channel import Channel


class ChannelTests(unittest.TestCase):
    def setUp(self):
        self.channel = Channel('#testing')

    def test_channel_has_name(self):
        self.assertEqual(self.channel.name, '#testing')

    def test_channel_convertable_to_string(self):
        self.assertEqual(str(self.channel), '#testing')

    def test_channel_repr(self):
        self.assertEqual(repr(self.channel), '<Channel #testing>')

    def test_channnel_empty_members(self):
        self.assertEqual(len(self.channel.members), 0)
