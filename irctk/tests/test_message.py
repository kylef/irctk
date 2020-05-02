import unittest
from irctk.message import Message


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

    def test_message_str(self):
        message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])

        self.assertEqual(str(message), 'PRIVMSG kyle :Hello World')

    def test_message_str_with_prefix(self):
        message = Message(prefix='doe!doe@example.com', command='PRIVMSG', parameters=['kyle', 'Hello World'])

        self.assertEqual(str(message), ':doe!doe@example.com PRIVMSG kyle :Hello World')
