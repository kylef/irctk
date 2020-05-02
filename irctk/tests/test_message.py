import unittest
from irctk.message import Message, MessageTag


class MessageTests(unittest.TestCase):
    def test_message_creation(self):
        message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])

        self.assertEqual(message.command, 'PRIVMSG')
        self.assertEqual(message.parameters, ['kyle', 'Hello World'])

    def test_parsing_message(self):
        message = Message.parse('PRIVMSG kyle :Hello World')

        self.assertEqual(message.command, 'PRIVMSG')
        self.assertEqual(message.parameters, ['kyle', 'Hello World'])

    def test_parsing_message_with_prefix(self):
        message = Message.parse(':doe!doe@example.com PRIVMSG kyle :Hello World')

        self.assertEqual(message.prefix, 'doe!doe@example.com')
        self.assertEqual(message.command, 'PRIVMSG')
        self.assertEqual(message.parameters, ['kyle', 'Hello World'])

    def test_parsing_message_with_tags(self):
        message = Message.parse('@time=2011-10-19T16:40:51.620Z :doe!doe@example.com PRIVMSG kyle :Hello World')

        self.assertEqual(len(message.tags), 1)
        self.assertEqual(message.tags[0].name, 'time')
        self.assertEqual(message.tags[0].value, '2011-10-19T16:40:51.620Z')
        self.assertEqual(message.prefix, 'doe!doe@example.com')
        self.assertEqual(message.command, 'PRIVMSG')
        self.assertEqual(message.parameters, ['kyle', 'Hello World'])

    def test_message_str(self):
        message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])

        self.assertEqual(str(message), 'PRIVMSG kyle :Hello World')

    def test_message_str_with_prefix(self):
        message = Message(prefix='doe!doe@example.com', command='PRIVMSG', parameters=['kyle', 'Hello World'])

        self.assertEqual(str(message), ':doe!doe@example.com PRIVMSG kyle :Hello World')

    def test_message_str_with_tags(self):
        tags = [MessageTag(name='time', value='2011-10-19T16:40:51.620Z')]
        message = Message(tags=tags, prefix='doe!doe@example.com', command='PRIVMSG', parameters=['kyle', 'Hello World'])

        self.assertEqual(str(message), '@time=2011-10-19T16:40:51.620Z :doe!doe@example.com PRIVMSG kyle :Hello World')
