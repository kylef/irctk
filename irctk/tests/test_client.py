import datetime
import unittest
from irctk.tests.mock_client import MockClient as Client
from irctk.nick import Nick
from irctk.message import Message


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

    def test_client_ignores_message_tags(self):
        self.client.read_data('@time=bar;foo=x :irc.kylefuller.co.uk 001 kyle :Welcome')
        self.assertTrue(self.client.is_registered)

    # Ping

    def test_client_sends_pong_when_pinged(self):
        self.client.read_data('PING :hello')
        self.assertEqual(self.client.sent_lines, ['PONG hello'])

    # Nick Change

    def test_clients_handles_nick_change(self):
        self.client.read_data(':irc.example.com 001 kyle :Welcome')
        self.client.read_data(':kyle!kyle@cocode.org NICK kyle2')
        self.assertEqual(self.client.nick.nick, 'kyle2')

    def test_clients_handles_nick_change_case_insensitive(self):
        self.client.read_data(':irc.example.com 001 kyle :Welcome')
        self.client.read_data(':KYLE!kyle@cocode.org NICK kyle2')
        self.assertEqual(self.client.nick.nick, 'kyle2')

    # Handling

    def test_client_handles_5_parsing_support(self):
        self.client.read_data(':irc.kylefuller.co.uk 005 kyle :NICKLEN=5 CHANNELLEN=6')
        self.assertEqual(self.client.isupport.maximum_nick_length, 5)
        self.assertEqual(self.client.isupport.maximum_channel_length, 6)

    def test_client_handles_joining_channel(self):
        self.client.read_data(':kylef!kyle@kyle JOIN #test')
        channel = self.client.channels[0]
        self.assertEqual(channel.members[0].nick.nick, self.client.nick.nick)

    def test_client_handles_parting_channel(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kylef!kyle@kyle JOIN #test')
        self.client.read_data(':kylef!kyle@kyle PART #test :goodbye')
        self.assertEqual(channel.members, [])

    def test_client_handles_parting_channel_without_reason(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kylef!kyle@kyle JOIN #test')
        self.client.read_data(':kylef!kyle@kyle PART #test')
        self.assertEqual(channel.members, [])

    def test_client_handles_getting_kicked_from_channel(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kylef!kyle@kyle JOIN #test')
        self.client.read_data(':kylef!kyle@kyle KICK #test kylef :goodbye')
        self.assertEqual(channel.members, [])

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

    def test_client_handles_353_names(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':server 353 kylef = #test :Derecho!der@der +Tempest!tmp@tmp dijit')
        self.assertEqual(len(channel.members), 3)
        self.assertEqual(channel.members[0].nick, Nick.parse('Derecho!der@der'))
        self.assertEqual(channel.members[1].nick, Nick.parse('Tempest!tmp@tmp'))
        self.assertEqual(channel.members[2].nick, Nick(nick='dijit'))
        self.assertTrue(channel.members[1].has_perm('v'))

    def test_client_updates_to_channel_topic(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kyle!kyle@kyle TOPIC #test :Hello World')
        self.assertEqual(channel.topic, 'Hello World')
        self.assertEqual(channel.topic_owner.nick, 'kyle')

    def test_client_updates_channel_membership_during_nick_change(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kyle!kyle@kyle JOIN #test')
        self.client.read_data(':kyle!kyle@kyle NICK kyle2')

        self.assertEqual(channel.members[0].nick.nick, 'kyle2')

    def test_client_updates_channel_membership_during_nick_change_case_insensitive(self):
        channel = self.client.add_channel('#test')
        self.client.read_data(':kyle!kyle@kyle JOIN #test')
        self.client.read_data(':KYLE!kyle@kyle NICK kyle2')

        self.assertEqual(channel.members[0].nick.nick, 'kyle2')

    # Capabilities

    def test_client_asks_for_server_capabilities_on_connection(self):
        self.client.authenticate()
        self.assertEqual(self.client.sent_lines[0], 'CAP LS')

    def test_client_ends_capabilities_negotiation_after_no_caps(self):
        self.client.authenticate()
        self.client.sent_lines = []  # reset, we dont care about auth stuff
        self.client.read_data(':barjavel.freenode.net CAP * LS :unknown-capability')
        self.assertEqual(self.client.sent_lines, ['CAP END'])

    def test_client_requests_multi_prefix_capability(self):
        self.client.authenticate()
        self.client.sent_lines = []  # reset, we dont care about auth stuff
        self.client.read_data(':barjavel.freenode.net CAP * LS :multi-prefix')
        self.assertEqual(self.client.sent_lines, ['CAP REQ multi-prefix'])
        self.client.sent_lines = []
        self.client.read_data(':barjavel.freenode.net CAP * ACK :multi-prefix')
        self.assertEqual(self.client.sent_lines, ['CAP END'])
        self.assertEqual(self.client.cap_accepted, ['multi-prefix'])

    # Delegate

    def test_client_forwards_private_messages_to_delegate(self):
        self.client.read_data(':bob!b@irc.kylefuller.co.uk PRIVMSG kylef :Hey')
        self.assertEqual(self.private_messages,
            [(self.client, Nick.parse('bob!b@irc.kylefuller.co.uk'), 'Hey')])

    # Sending

    def test_client_send_message(self):
        message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])
        self.client.send(message)

        self.assertEqual(self.client.sent_lines, [
            'PRIVMSG kyle :Hello World'
        ])

    def test_client_send_privmsg(self):
        self.client.send_privmsg('kyle', 'Hello')
        self.assertEqual(self.client.sent_lines, [
            'PRIVMSG kyle :Hello'
        ])

    def test_client_send_join(self):
        self.client.send_join('#palaver')
        self.assertEqual(self.client.sent_lines, [
            'JOIN #palaver'
        ])

    def test_client_send_join_with_key(self):
        self.client.send_join('#palaver', 'secret')
        self.assertEqual(self.client.sent_lines, [
            'JOIN #palaver secret'
        ])

    def test_client_send_part(self):
        self.client.send_part('#palaver')
        self.assertEqual(self.client.sent_lines, [
            'PART #palaver'
        ])
