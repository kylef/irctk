import unittest

from irctk.message import Message, MessageTag

# Message Tags


def test_parse_name() -> None:
    tag = MessageTag.parse('account')

    assert tag.vendor is None
    assert tag.name == 'account'
    assert tag.value is None


def test_parse_vendor() -> None:
    tag = MessageTag.parse('draft/account')

    assert tag.vendor == 'draft'
    assert tag.name == 'account'
    assert tag.value is None


def test_parse_value() -> None:
    tag = MessageTag.parse('account=doe')

    assert tag.vendor is None
    assert tag.name == 'account'
    assert tag.value == 'doe'


def test_parse_escaped_value() -> None:
    tag = MessageTag.parse('+example=raw+:=,escaped\\:\\s\\\\')

    assert tag.is_client_only
    assert tag.vendor is None
    assert tag.name == 'example'
    assert tag.value == 'raw+:=,escaped; \\'


def test_to_string() -> None:
    tag = MessageTag(vendor='draft', name='example', value='raw+:=,escaped; \\')

    assert str(tag) == 'draft/example=raw+:=,escaped\\:\\s\\\\'


# Message


def test_message_creation() -> None:
    message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])

    assert message.command == 'PRIVMSG'
    assert message.parameters == ['kyle', 'Hello World']


def test_parsing_message() -> None:
    message = Message.parse('PRIVMSG kyle :Hello World')

    assert message.command == 'PRIVMSG'
    assert message.parameters == ['kyle', 'Hello World']


def test_parsing_message_with_prefix() -> None:
    message = Message.parse(':doe!doe@example.com PRIVMSG kyle :Hello World')

    assert message.prefix == 'doe!doe@example.com'
    assert message.command == 'PRIVMSG'
    assert message.parameters == ['kyle', 'Hello World']


def test_parsing_message_with_tags() -> None:
    message = Message.parse(
        '@time=2011-10-19T16:40:51.620Z :doe!doe@example.com PRIVMSG kyle :Hello World'
    )

    assert len(message.tags) == 1
    assert message.tags[0].name == 'time'
    assert message.tags[0].value == '2011-10-19T16:40:51.620Z'
    assert message.prefix == 'doe!doe@example.com'
    assert message.command == 'PRIVMSG'
    assert message.parameters == ['kyle', 'Hello World']


def test_parsing_message_with_command() -> None:
    message = Message.parse('PING')

    assert message.command == 'PING'


def test_message_str() -> None:
    message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])

    assert str(message) == 'PRIVMSG kyle :Hello World'


def test_message_str_with_prefix() -> None:
    message = Message(
        prefix='doe!doe@example.com',
        command='PRIVMSG',
        parameters=['kyle', 'Hello World'],
    )

    assert str(message) == ':doe!doe@example.com PRIVMSG kyle :Hello World'


def test_message_str_with_tags() -> None:
    tags = [MessageTag(name='time', value='2011-10-19T16:40:51.620Z')]
    message = Message(
        tags=tags,
        prefix='doe!doe@example.com',
        command='PRIVMSG',
        parameters=['kyle', 'Hello World'],
    )

    assert (
        str(message)
        == '@time=2011-10-19T16:40:51.620Z :doe!doe@example.com PRIVMSG kyle :Hello World'
    )


def test_message_bytes() -> None:
    message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])

    assert bytes(message) == b'PRIVMSG kyle :Hello World\r\n'


def test_message_find_tag() -> None:
    message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])
    message.tags.append(MessageTag(name='account', value='kyle'))
    message.tags.append(
        MessageTag(is_client_only=True, vendor='draft', name='reply', value='mid')
    )

    assert message.find_tag('unknown') is None

    assert message.find_tag('account') is 'kyle'
    assert message.find_tag('account', vendor='vendor') is None
    assert message.find_tag('account', is_client_only=True) is None

    assert message.find_tag('reply') is None
    assert message.find_tag('reply', vendor='draft') is None
    assert message.find_tag('reply', vendor='draft', is_client_only=True) is 'mid'


def test_account() -> None:
    message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])
    assert message.account is None

    message.tags.append(MessageTag(name='account', value='kyle'))
    assert message.account is 'kyle'


def test_label() -> None:
    message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])
    assert message.label is None

    message.tags.append(MessageTag(name='label', value='079cda68'))
    assert message.label is '079cda68'


def test_batch() -> None:
    message = Message(command='PRIVMSG', parameters=['kyle', 'Hello World'])
    assert message.batch is None

    message.tags.append(MessageTag(name='batch', value='079cda68'))
    assert message.batch is '079cda68'
