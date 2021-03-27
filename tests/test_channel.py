import unittest

from irctk.channel import Channel, Membership
from irctk.isupport import ISupport
from irctk.nick import Nick


class ChannelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.channel = Channel('#testing')

    def test_channel_has_name(self) -> None:
        self.assertEqual(self.channel.name, '#testing')

    def test_channel_convertable_to_string(self) -> None:
        self.assertEqual(str(self.channel), '#testing')

    def test_channel_repr(self) -> None:
        self.assertEqual(repr(self.channel), '<Channel #testing>')

    def test_channnel_empty_members(self) -> None:
        self.assertEqual(len(self.channel.members), 0)

    # MODE

    def test_channel_set_user_mode(self) -> None:
        membership = Membership(Nick('kyle'))
        self.channel.members.append(membership)

        self.channel.mode_change('+o kyle', ISupport())

        self.assertTrue(membership.has_mode('o'))

    def test_channel_unset_user_mode(self) -> None:
        membership = Membership(Nick('kyle'), ['o', 'v'])
        self.channel.members.append(membership)

        self.channel.mode_change('-o kyle', ISupport())

        self.assertFalse(membership.has_mode('o'))
        self.assertTrue(membership.has_mode('v'))

    def test_channel_set_mode_with_arg(self) -> None:
        self.channel.mode_change('+k sekret', ISupport())

        self.assertEqual(self.channel.modes['k'], 'sekret')

    def test_channel_unset_mode_with_arg(self) -> None:
        self.channel.modes['k'] = 'sekret'
        self.channel.mode_change('-k sekret', ISupport())

        self.assertTrue('k' not in self.channel.modes)
