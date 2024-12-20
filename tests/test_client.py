import datetime
import unittest
from typing import List

from irctk.message import Message, MessageTag
from irctk.nick import Nick
from tests.mock_client import MockClient as Client


class ClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Client('kylef', 'kyle', 'Kyle Fuller')
        self.client.nick.nick = 'kylef'
        self.client.delegate = self

        self.private_messages: List = []
        self.channel_messages: List = []

    # Delegate

    def irc_private_message(self, client, nick, message):
        self.private_messages.append((client, nick, message))

    def irc_channel_message(self, client, nick, channel, message):
        self.channel_messages.append((client, nick, channel, message))

    def test_set_delegate(self) -> None:
        self.client.delegate = self
        self.assertEqual(self.client.delegate, self)

    # Tests

    def test_client_has_nickname(self) -> None:
        self.assertEqual(self.client.nickname, 'kylef')

    def test_client_has_ident(self) -> None:
        self.assertEqual(self.client.ident, 'kyle')

    def test_client_has_realname(self) -> None:
        self.assertEqual(self.client.realname, 'Kyle Fuller')

    # Registration

    def test_client_is_not_registered_by_default(self) -> None:
        self.assertFalse(self.client.is_registered)

    def test_client_is_registered_after_001(self) -> None:
        self.client.process_line(':irc.kylefuller.co.uk 001 kyle :Welcome')
        self.assertTrue(self.client.is_registered)

    def test_client_takes_nick_from_001(self) -> None:
        self.client.process_line(':irc.kylefuller.co.uk 001 kyle5 :Welcome')
        self.assertEqual(self.client.nick.nick, 'kyle5')

    def test_client_ignores_message_tags(self) -> None:
        self.client.process_line(
            '@time=bar;foo=x :irc.kylefuller.co.uk 001 kyle :Welcome'
        )
        self.assertTrue(self.client.is_registered)

    # Ping

    def test_client_sends_pong_when_pinged(self) -> None:
        self.client.process_line('PING :hello')
        self.assertEqual(self.client.sent_lines, ['PONG hello'])

    # Nick Change

    def test_clients_handles_nick_change(self) -> None:
        self.client.process_line(':irc.example.com 001 kyle :Welcome')
        self.client.process_line(':kyle!kyle@cocode.org NICK kyle2')
        self.assertEqual(self.client.nick.nick, 'kyle2')

    def test_clients_handles_nick_change_case_insensitive(self) -> None:
        self.client.process_line(':irc.example.com 001 kyle :Welcome')
        self.client.process_line(':KYLE!kyle@cocode.org NICK kyle2')
        self.assertEqual(self.client.nick.nick, 'kyle2')

    # Handling

    def test_client_handles_5_parsing_support(self) -> None:
        self.client.process_line(
            ':irc.kylefuller.co.uk 005 kyle :NICKLEN=5 CHANNELLEN=6'
        )
        self.assertEqual(self.client.isupport.maximum_nick_length, 5)
        self.assertEqual(self.client.isupport.maximum_channel_length, 6)

    def test_client_handles_joining_channel(self) -> None:
        self.client.process_line(':kylef!kyle@kyle JOIN #test')

        channel = self.client.channels[0]
        self.assertEqual(channel.name, '#test')
        self.assertEqual(channel.members[0].nick.nick, self.client.nick.nick)
        self.assertTrue(channel.is_attached)

    def test_client_handles_parting_channel(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':kylef!kyle@kyle JOIN #test')
        self.client.process_line(':kylef!kyle@kyle PART #test :goodbye')
        self.assertEqual(channel.members, [])
        self.assertFalse(channel.is_attached)

    def test_client_handles_parting_channel_without_reason(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':kylef!kyle@kyle JOIN #test')
        self.client.process_line(':kylef!kyle@kyle PART #test')
        self.assertEqual(channel.members, [])

    def test_client_handles_quit_removing_from_channel(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':kylef!kyle@kyle JOIN #test')

        self.client.process_line(':doe!kyle@kyle JOIN #test')
        self.assertEqual(len(channel.members), 2)

        self.client.process_line(':doe!kyle@kyle QUIT :goodbye')
        self.assertEqual(len(channel.members), 1)

    def test_client_handles_getting_kicked_from_channel(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':kylef!kyle@kyle JOIN #test')
        self.client.process_line(':kylef!kyle@kyle KICK #test kylef :goodbye')
        self.assertEqual(channel.members, [])

    def test_client_handles_channel_new_mode(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':kyle!kyle@kyle MODE #test +tn')
        self.assertTrue(channel.modes['t'])
        self.assertTrue(channel.modes['n'])

    def test_client_handles_channel_remove_mode(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':kyle!kyle@kyle MODE #test +tn')
        self.client.process_line(':kyle!kyle@kyle MODE #test -tn')
        self.assertEqual(channel.modes, {})

    def test_client_handles_setting_channel_list_mode(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':kyle!kyle@kyle MODE #test +b cake')
        self.client.process_line(':kyle!kyle@kyle MODE #test +b snake')
        self.assertEqual(channel.modes['b'], ['cake', 'snake'])

    def test_client_handles_removing_channel_list_mode(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':kyle!kyle@kyle MODE #test +b cake')
        self.client.process_line(':kyle!kyle@kyle MODE #test +b snake')
        self.client.process_line(':kyle!kyle@kyle MODE #test -b cake')
        self.assertEqual(channel.modes['b'], ['snake'])

    def test_client_handles_removing_channel_list_mode2(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':kyle!kyle@kyle MODE #test +l 5')
        self.client.process_line(':kyle!kyle@kyle MODE #test +l 6')
        self.assertEqual(channel.modes['l'], '6')

    def test_client_handles_324_mode(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':server 324 kylef #test +nt')
        self.assertEqual(channel.modes, {'n': True, 't': True})

    def test_client_handles_329_creation_date(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':server 329 kylef #test 1358579621')
        self.assertEqual(
            channel.creation_date, datetime.datetime(2013, 1, 19, 7, 13, 41)
        )

    def test_client_handles_332_topic(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':server 332 kylef #test :My Awesome Topic')
        self.assertEqual(channel.topic, 'My Awesome Topic')

    def test_client_handles_333_topic(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':server 333 kylef #test james!james@james 1395663680')
        self.assertEqual(channel.topic_owner, 'james!james@james')
        self.assertEqual(channel.topic_date, datetime.datetime(2014, 3, 24, 12, 21, 20))

    def test_client_handles_352(self) -> None:
        self.client.process_line(
            ':server 352 kylef * ~doe example.com irc-eu-1.darkscience.net kylef Hs :0 irctk'
        )
        self.assertEqual(self.client.nick.ident, '~doe')
        self.assertEqual(self.client.nick.host, 'example.com')

    def test_client_handles_353_names(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(
            ':server 353 kylef = #test :Derecho!der@der +Tempest!tmp@tmp dijit +other'
        )
        self.assertEqual(len(channel.members), 4)
        self.assertEqual(channel.members[0].nick, Nick.parse('Derecho!der@der'))
        self.assertEqual(channel.members[1].nick, Nick.parse('Tempest!tmp@tmp'))
        self.assertEqual(channel.members[2].nick, Nick(nick='dijit'))
        self.assertEqual(channel.members[3].nick, Nick(nick='other'))
        self.assertTrue(channel.members[1].has_mode('v'))
        self.assertTrue(channel.members[3].has_mode('v'))

    def test_client_updates_to_channel_topic(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':kyle!kyle@kyle TOPIC #test :Hello World')
        self.assertEqual(channel.topic, 'Hello World')

        assert isinstance(channel.topic_owner, Nick)
        self.assertEqual(channel.topic_owner.nick, 'kyle')

    def test_client_updates_channel_membership_during_nick_change(self) -> None:
        channel = self.client.add_channel('#test')
        self.client.process_line(':kyle!kyle@kyle JOIN #test')
        self.client.process_line(':kyle!kyle@kyle NICK kyle2')

        self.assertEqual(channel.members[0].nick.nick, 'kyle2')

    def test_client_updates_channel_membership_during_nick_change_case_insensitive(
        self,
    ):
        channel = self.client.add_channel('#test')
        self.client.process_line(':kyle!kyle@kyle JOIN #test')
        self.client.process_line(':KYLE!kyle@kyle NICK kyle2')

        self.assertEqual(channel.members[0].nick.nick, 'kyle2')

    # Capabilities

    def test_client_asks_for_server_capabilities_on_connection(self) -> None:
        self.client.authenticate()
        self.assertEqual(self.client.sent_lines[0], 'CAP LS')

    def test_client_ends_capabilities_negotiation_after_no_caps(self) -> None:
        self.client.authenticate()
        self.client.sent_lines = []  # reset, we dont care about auth stuff
        self.client.process_line(':barjavel.freenode.net CAP * LS :unknown-capability')
        self.assertEqual(self.client.sent_lines, ['CAP END'])

    def test_client_requests_multi_prefix_capability(self) -> None:
        self.client.authenticate()
        self.client.sent_lines = []  # reset, we dont care about auth stuff
        self.client.process_line(':barjavel.freenode.net CAP * LS :multi-prefix')
        self.assertEqual(self.client.sent_lines, ['CAP REQ multi-prefix'])
        self.client.sent_lines = []
        self.client.process_line(':barjavel.freenode.net CAP * ACK :multi-prefix')
        self.assertEqual(self.client.sent_lines, ['CAP END'])
        self.assertEqual(self.client.cap_accepted, ['multi-prefix'])

    def test_client_requests_multi_prefix_capability_and_handles_rejection(
        self,
    ) -> None:
        self.client.authenticate()
        self.client.sent_lines = []  # reset, we dont care about auth stuff
        self.client.process_line(':barjavel.freenode.net CAP * LS :multi-prefix')
        self.assertEqual(self.client.sent_lines, ['CAP REQ multi-prefix'])
        self.client.sent_lines = []
        self.client.process_line(':barjavel.freenode.net CAP * NAK :multi-prefix')
        self.assertEqual(self.client.sent_lines, ['CAP END'])
        self.assertEqual(self.client.cap_accepted, [])

    # Perform

    def test_client_perform_on_connect(self) -> None:
        self.client.authenticate()

        self.assertEqual(
            self.client.sent_lines,
            ['CAP LS', 'NICK kylef', 'USER kyle 0 * :Kyle Fuller'],
        )

    def test_client_perform_on_connect_with_password(self) -> None:
        self.client.password = 'sekret'
        self.client.authenticate()

        self.assertEqual(
            self.client.sent_lines,
            ['CAP LS', 'PASS sekret', 'NICK kylef', 'USER kyle 0 * :Kyle Fuller'],
        )

    # Delegate

    def test_client_forwards_private_messages_to_delegate(self) -> None:
        self.client.process_line(':bob!b@irc.kylefuller.co.uk PRIVMSG kylef :Hey')
        self.assertEqual(
            self.private_messages,
            [(self.client, Nick.parse('bob!b@irc.kylefuller.co.uk'), 'Hey')],
        )

    def test_client_forwards_channel_messages_to_delegate(self) -> None:
        self.client.process_line(':kylef!b@irc.kylefuller.co.uk JOIN #example')
        self.client.process_line(':bob!b@irc.kylefuller.co.uk PRIVMSG #example :Hey')

        self.assertEqual(len(self.channel_messages), 1)
        self.assertEqual(self.channel_messages[0][1].nick, 'bob')
        self.assertEqual(self.channel_messages[0][2].name, '#example')
        self.assertEqual(self.channel_messages[0][3], 'Hey')

    # Sending

    def test_client_send_message(self) -> None:
        message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])
        self.client.send(message)

        self.assertEqual(self.client.sent_lines, ['PRIVMSG kyle :Hello World'])

    def test_client_send_message_bad_args(self) -> None:
        message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])

        with self.assertRaises(TypeError):
            self.client.send(message, 'x')

    def test_client_send_privmsg(self) -> None:
        self.client.send_privmsg('kyle', 'Hello')
        self.assertEqual(self.client.sent_lines, ['PRIVMSG kyle :Hello'])

    def test_client_send_notice(self) -> None:
        self.client.send_notice('kyle', 'Hello')
        self.assertEqual(self.client.sent_lines, ['NOTICE kyle :Hello'])

    def test_client_send_join(self) -> None:
        self.client.send_join('#palaver')
        self.assertEqual(self.client.sent_lines, ['JOIN #palaver'])

    def test_client_send_join_with_key(self) -> None:
        self.client.send_join('#palaver', 'secret')
        self.assertEqual(self.client.sent_lines, ['JOIN #palaver secret'])

    def test_client_send_part(self) -> None:
        self.client.send_part('#palaver')
        self.assertEqual(self.client.sent_lines, ['PART #palaver'])

    def test_client_send_label_message(self) -> None:
        message = Message(command='PING', parameters=['localhost'])
        message.tags.append(MessageTag(name='label', value='xx'))
        future = self.client.send(message)
        self.assertFalse(future.done())

        self.assertEqual(self.client.sent_lines, ['@label=xx PING localhost'])

        self.client.process_line('@label=xx PONG localhost')
        self.assertTrue(future.done())
        self.assertEqual(str(future.result()), '@label=xx PONG localhost')

    def test_client_send_label_message_ack(self) -> None:
        message = Message(command='PONG', parameters=['localhost'])
        message.tags.append(MessageTag(name='label', value='xx'))
        future = self.client.send(message)
        self.assertFalse(future.done())

        self.assertEqual(self.client.sent_lines, ['@label=xx PONG localhost'])

        self.client.process_line('@label=xx :irc.example.com ACK')
        self.assertTrue(future.done())
        self.assertEqual(str(future.result()), '@label=xx :irc.example.com ACK')

    def test_client_send_label_message_batch(self) -> None:
        message = Message(command='WHOIS', parameters=['kyle'])
        message.tags.append(MessageTag(name='label', value='mGhe5V7RTV'))
        future = self.client.send(message)

        self.assertEqual(self.client.sent_lines, ['@label=mGhe5V7RTV WHOIS kyle'])

        self.client.process_line(
            '@label=mGhe5V7RTV :irc.example.com BATCH +NMzYSq45x labeled-response'
        )
        self.client.process_line(
            '@batch=NMzYSq45x :irc.example.com 311 client nick ~ident host * :Name'
        )
        self.client.process_line(
            '@batch=NMzYSq45x :irc.example.com 318 client nick :End of /WHOIS list.'
        )
        self.assertFalse(future.done())

        self.client.process_line(':irc.example.com BATCH -NMzYSq45x')
        self.assertTrue(future.done())
        self.assertEqual(
            [str(m) for m in future.result()],
            [
                '@label=mGhe5V7RTV :irc.example.com BATCH +NMzYSq45x labeled-response',
                '@batch=NMzYSq45x :irc.example.com 311 client nick ~ident host * Name',
                '@batch=NMzYSq45x :irc.example.com 318 client nick :End of /WHOIS list.',
                ':irc.example.com BATCH -NMzYSq45x',
            ],
        )

    def test_client_send_nick(self) -> None:
        message = Message(command='NICK', parameters=['newnick'])
        future = self.client.send(message)

        self.assertFalse(future.done())
        self.assertEqual(self.client.sent_lines, ['NICK newnick'])

        self.client.process_line(':kylef NICK newnick')
        self.assertTrue(future.done())
        self.assertEqual(str(future.result()), ':kylef NICK newnick')

    def test_client_send_nick_no_nickname_given(self) -> None:
        message = Message(command='NICK', parameters=[])
        future = self.client.send(message)

        self.assertFalse(future.done())
        self.assertEqual(self.client.sent_lines, ['NICK'])

        self.client.process_line(':example.com 431 kylef :No nickname given')
        self.assertTrue(future.done())

    def test_client_send_nick_erroneus_nickname(self) -> None:
        message = Message(command='NICK', parameters=['doe'])
        future = self.client.send(message)

        self.assertFalse(future.done())
        self.assertEqual(self.client.sent_lines, ['NICK doe'])

        self.client.process_line(':example.com 432 kylef doe :Erroneus nickname')
        self.assertTrue(future.done())

    def test_client_send_nick_nickname_in_use(self) -> None:
        message = Message(command='NICK', parameters=['doe'])
        future = self.client.send(message)

        self.assertFalse(future.done())
        self.assertEqual(self.client.sent_lines, ['NICK doe'])

        self.client.process_line(
            ':example.com 433 kylef doe :Nickname is already in use'
        )
        self.assertTrue(future.done())

    def test_client_send_nick_nick_collision(self) -> None:
        message = Message(command='NICK', parameters=['doe'])
        future = self.client.send(message)

        self.assertFalse(future.done())
        self.assertEqual(self.client.sent_lines, ['NICK doe'])

        self.client.process_line(':example.com 436 kylef doe :Nickname collision KILL')
        self.assertTrue(future.done())

    def test_client_send_nick_complete_registration(self) -> None:
        message = Message(command='NICK', parameters=['doe'])
        future = self.client.send(message)

        self.assertFalse(future.done())
        self.assertEqual(self.client.sent_lines, ['NICK doe'])

        self.client.process_line(':irc.example.com 001 doe :Welcome')
        self.assertTrue(future.done())
