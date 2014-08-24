import datetime
import unittest
from irctk.tests.mock_client import MockClient as Client
from irctk.nick import Nick


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.client = Client('kylef', 'kyle', 'Kyle Fuller')
        self.client.nick.nick = 'kylef'
        self.client.delegate = self

        self.private_messages = []

    # Delegate

    def irc_private_message(self, client, nick, message):
        self.private_messages.append((client, nick, message))

    # Tests

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
        self.assertEqual(self.client.sent_lines, ['PONG hello'])

    # Handling

    def test_client_handles_5_parsing_support(self):
        self.client.read_data(':irc.kylefuller.co.uk 005 kyle :NICKLEN=5 CHANNELLEN=6')
        self.assertEqual(self.client.isupport.maximum_nick_length, 5)
        self.assertEqual(self.client.isupport.maximum_channel_length, 6)

    def test_client_handles_joining_channel(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kylef!kyle@kyle JOIN #test')
        self.assertEqual(channel.nicks, [self.client.nick])

    def test_client_handles_parting_channel(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kylef!kyle@kyle JOIN #test')
        self.client.read_data(':kylef!kyle@kyle PART #test :goodbye')
        self.assertEqual(channel.nicks, [])

    def test_client_handles_parting_channel_without_reason(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kylef!kyle@kyle JOIN #test')
        self.client.read_data(':kylef!kyle@kyle PART #test')
        self.assertEqual(channel.nicks, [])

    def test_client_handles_getting_kicked_from_channel(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kylef!kyle@kyle JOIN #test')
        self.client.read_data(':kylef!kyle@kyle KICK #test kylef :goodbye')
        self.assertEqual(channel.nicks, [])

    def test_client_handles_channel_new_mode(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kyle!kyle@kyle MODE #test +tn')
        self.assertTrue(channel.modes['t'])
        self.assertTrue(channel.modes['n'])

    def test_client_handles_channel_remove_mode(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kyle!kyle@kyle MODE #test +tn')
        self.client.read_data(':kyle!kyle@kyle MODE #test -tn')
        self.assertEqual(channel.modes, {})

    def test_client_handles_setting_channel_list_mode(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kyle!kyle@kyle MODE #test +b cake')
        self.client.read_data(':kyle!kyle@kyle MODE #test +b snake')
        self.assertEqual(channel.modes['b'], ['cake', 'snake'])

    def test_client_handles_removing_channel_list_mode(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kyle!kyle@kyle MODE #test +b cake')
        self.client.read_data(':kyle!kyle@kyle MODE #test +b snake')
        self.client.read_data(':kyle!kyle@kyle MODE #test -b cake')
        self.assertEqual(channel.modes['b'], ['snake'])

    def test_client_handles_removing_channel_list_mode(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kyle!kyle@kyle MODE #test +l 5')
        self.client.read_data(':kyle!kyle@kyle MODE #test +l 6')
        self.assertEqual(channel.modes['l'], '6')

    def test_client_handles_324_mode(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':server 324 kylef #test +nt')
        self.assertEqual(channel.modes, {'n': True, 't': True})

    def test_client_handles_329_creation_date(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':server 329 kylef #test 1358579621')
        self.assertEqual(channel.creation_date, datetime.datetime(2013, 1, 19, 7, 13, 41))

    def test_client_handles_332_topic(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':server 332 kylef #test :My Awesome Topic')
        self.assertEqual(channel.topic, 'My Awesome Topic')

    def test_client_handles_333_topic(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':server 333 kylef #test james!james@james 1395663680')
        self.assertEqual(channel.topic_owner, 'james!james@james')
        self.assertEqual(channel.topic_date, datetime.datetime(2014, 3, 24, 12, 21, 20))

    def test_client_updates_to_channel_topic(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kyle!kyle@kyle TOPIC #test :Hello World')
        self.assertEqual(channel.topic, 'Hello World')
        self.assertEqual(channel.topic_owner, 'kyle')

    # Delegate

    def test_client_forwards_private_messages_to_delegate(self):
        self.client.read_data(':bob!b@irc.kylefuller.co.uk PRIVMSG kylef :Hey')
        self.assertEqual(self.private_messages,
            [(self.client, Nick.parse(self.client, 'bob!b@irc.kylefuller.co.uk'), 'Hey')])

