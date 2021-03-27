import unittest

from irctk.nick import Nick


def test_nick_initialization() -> None:
    nick = Nick('kylef', 'ident', 'example.com')

    assert nick.nick == 'kylef'
    assert nick.ident == 'ident'
    assert nick.host == 'example.com'


def test_nick_parsing_from_userhost() -> None:
    nick = Nick.parse('kylef!ident@example.com')

    assert nick.nick == 'kylef'
    assert nick.ident == 'ident'
    assert nick.host == 'example.com'


def test_nick_parsing_from_hostname() -> None:
    nick = Nick.parse('example.com')

    assert nick.host == 'example.com'


def test_conversion_to_string() -> None:
    nick = Nick('kylef', 'ident', 'example.com')

    assert str(nick) == 'kylef'


def test_nick_repr() -> None:
    nick = Nick('kylef', 'ident', 'example.com')

    assert repr(nick) == '<Nick kylef!ident@example.com>'
