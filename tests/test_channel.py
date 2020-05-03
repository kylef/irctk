import unittest
from irctk.isupport import ISupport
from irctk.nick import Nick
from irctk.channel import Channel, Membership


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

    # MODE

    def test_channel_set_user_mode(self):
        membership = Membership(Nick('kyle'))
        self.channel.members.append(membership)

        self.channel.mode_change('+o kyle', ISupport())

        self.assertTrue(membership.has_perm('o'))

    def test_channel_unset_user_mode(self):
        membership = Membership(Nick('kyle'), ['o', 'v'])
        self.channel.members.append(membership)

        self.channel.mode_change('-o kyle', ISupport())

        self.assertFalse(membership.has_perm('o'))
        self.assertTrue(membership.has_perm('v'))

    def test_channel_set_mode_with_arg(self):
        self.channel.mode_change('+k sekret', ISupport())

        self.assertEqual(self.channel.modes['k'], 'sekret')

    def test_channel_unset_mode_with_arg(self):
        self.channel.modes['k'] = 'sekret'
        self.channel.mode_change('-k sekret', ISupport())

        self.assertTrue('k' not in self.channel.modes)
