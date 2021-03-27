import unittest

import pytest

from irctk.isupport import ISupport


@pytest.fixture()
def isupport() -> ISupport:
    return ISupport()


# Defaults


def test_default_maximum_nick_length(isupport: ISupport) -> None:
    assert isupport.maximum_nick_length == 9


def test_default_maximum_channel_length(isupport: ISupport) -> None:
    assert isupport.maximum_channel_length == 200


def test_default_channel_prefixes(isupport: ISupport) -> None:
    assert isupport.channel_prefixes == ['#', '&']


def test_default_user_channel_modes(isupport: ISupport) -> None:
    assert isupport['prefix'] == {'o': '@', 'v': '+'}


def test_default_case_mapping(isupport: ISupport) -> None:
    assert isupport.case_mapping == 'rfc1459'


# Is channel


def test_is_channel_disallows_commas(isupport: ISupport) -> None:
    assert not isupport.is_channel('#te,st')


def test_is_channel_disallows_spaces(isupport: ISupport) -> None:
    assert not isupport.is_channel('#te st')


def test_is_channel_allows_channels_with_channel_prefix(isupport: ISupport) -> None:
    isupport['chantypes'] = ['$']
    assert isupport.is_channel('$test')


def test_is_channel_disallows_chanels_without_channel_prefix(
    isupport: ISupport,
) -> None:
    assert not isupport.is_channel('$test')


def test_is_channel_disallows_channels_exceeding_maximum_length(
    isupport: ISupport,
) -> None:
    isupport['channellen'] = 5
    assert not isupport.is_channel('#testing')


# Test parsing


def test_can_parse_nicklen(isupport: ISupport) -> None:
    isupport.parse('NICKLEN=5')
    assert isupport.maximum_nick_length == 5


def test_can_parse_channellen(isupport: ISupport) -> None:
    isupport.parse('CHANNELLEN=10')
    assert isupport.maximum_channel_length == 10


def test_can_parse_prefix(isupport: ISupport) -> None:
    isupport.parse('PREFIX=(ohv)$%+')
    assert isupport['prefix'] == {'o': '$', 'h': '%', 'v': '+'}


def test_can_parse_chanmodes(isupport: ISupport) -> None:
    isupport.parse('CHANMODES=ae,bf,cg,dh')
    assert isupport['chanmodes'] == {
        'a': list,
        'e': list,
        'b': 'arg',
        'f': 'arg',
        'c': 'arg_set',
        'g': 'arg_set',
        'd': None,
        'h': None,
    }


def test_can_parse_chantypes(isupport: ISupport) -> None:
    isupport.parse('CHANTYPES=$^')
    assert isupport['chantypes'] == ['$', '^']


def test_can_parse_removal(isupport: ISupport) -> None:
    isupport.parse('MONITOR')
    assert 'MONITOR' in isupport

    isupport.parse('-MONITOR')
    assert 'MONITOR' not in isupport


def test_can_parse_removal_reverts_to_default(isupport: ISupport) -> None:
    isupport.parse('CASEMAPPING=ascii')
    assert isupport.case_mapping == 'ascii'

    isupport.parse('-CASEMAPPING')
    assert isupport.case_mapping == 'rfc1459'


# Test construction


def test_can_be_converted_to_string(isupport: ISupport) -> None:
    line = str(isupport)

    new_support = ISupport()
    new_support.clear()
    new_support.parse(line)

    assert new_support == isupport
