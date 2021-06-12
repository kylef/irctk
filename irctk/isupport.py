import re
from typing import List, Optional

DEFAULT_ISUPPORT = {
    'casemapping': 'rfc1459',
    'chanmodes': {
        'b': list,
        'e': list,
        'I': list,
        'k': 'arg',
        'l': 'arg_set',
        'p': None,
        's': None,
        't': None,
        'i': None,
        'n': None,
    },
    'prefix': {'o': '@', 'v': '+'},
    'channellen': 200,
    'chantypes': ['#', '&'],
    'modes': 3,
    'nicklen': 9,
    # Unlimited
    'topiclen': 0,
    'kicklen': 0,
    'modes': 0,
}


class ISupport(dict):
    IRC_ISUPPORT_PREFIX = re.compile(r'^\((.+)\)(.+)$')

    def __init__(self):
        self.update(DEFAULT_ISUPPORT)

    def __str__(self) -> str:
        values = []

        for key in self:
            method = getattr(self, 'to_str_{}'.format(key), None)
            if method:
                value = method()
            else:
                value = self[key]

            if value is not None:
                if value is True:
                    value = '1'
                elif value is False:
                    value = '0'
                elif isinstance(value, list):
                    value = ''.join(value)

                values.append('{}={}'.format(key.upper(), value))
            else:
                values.append(key.upper())

        return ' '.join(values)

    def to_str_chanmodes(self) -> str:
        chanmodes = self.get('chanmodes', {})
        list_args, arg, arg_set, no_args = [], [], [], []

        for mode in chanmodes:
            value = chanmodes[mode]

            if value is list:
                list_args.append(mode)
            elif value == 'arg':
                arg.append(mode)
            elif value == 'arg_set':
                arg_set.append(mode)
            elif value is None:
                no_args.append(mode)

        return ','.join(
            map(lambda modes: ''.join(modes), [list_args, arg, arg_set, no_args])
        )

    def to_str_prefix(self) -> str:
        prefix = self.get('prefix', {})

        modes = ''
        prefixes = ''

        for mode in prefix:
            modes += mode
            prefixes += prefix[mode]

        return '({}){}'.format(modes, prefixes)

    # Parsing

    def parse(self, line: str) -> None:
        for pair in line.split():
            if '=' not in pair:
                if pair.startswith('-'):
                    key = pair[1:]
                    if key.lower() in DEFAULT_ISUPPORT:
                        self[key.lower()] = DEFAULT_ISUPPORT[key.lower()]
                    elif key in self:
                        del self[key]

                    continue

                self[pair] = None
                continue

            key, value = pair.split('=', 1)

            if key == 'PREFIX':
                self.parse_prefix(value)
            elif key == 'CHANMODES':
                self.parse_chanmodes(value)
            elif key == 'CHANTYPES':
                self['chantypes'] = list(value)
            elif key in (
                'CHANNELLEN',
                'NICKLEN',
                'MODES',
                'TOPICLEN',
                'KICKLEN',
                'MODES',
            ):
                self[key.lower()] = int(value)
            elif key == 'CASEMAPPING':
                self[key.lower()] = value
            else:
                self[key] = value

    def parse_prefix(self, value: str) -> None:
        self['prefix'] = {}

        m = self.IRC_ISUPPORT_PREFIX.match(value)
        if m and len(m.group(1)) == len(m.group(2)):
            for x in range(0, len(m.group(1))):
                self['prefix'][m.group(1)[x]] = m.group(2)[x]

    def parse_chanmodes(self, value: str) -> None:
        try:
            list_args, arg, arg_set, no_args = value.split(',')
        except ValueError:
            return

        self['chanmodes'] = {}

        for mode in list_args:
            self['chanmodes'][mode] = list

        for mode in arg:
            self['chanmodes'][mode] = 'arg'

        for mode in arg_set:
            self['chanmodes'][mode] = 'arg_set'

        for mode in no_args:
            self['chanmodes'][mode] = None

    # Get

    @property
    def maximum_nick_length(self) -> int:
        """
        Returns the maximum length of a nickname.

        Example::

            >>> support.maximum_nick_length
            9
        """
        return self['nicklen']

    @property
    def maximum_channel_length(self) -> int:
        """
        Returns the maximum length of a channel name.

        Example::

            >>> support.maximum_channel_length
            200
        """
        return self['channellen']

    @property
    def channel_prefixes(self) -> List[str]:
        """
        Returns a list of channel prefixes.

        Example::

            >>> support.channel_prefixes
            ['#', '&']
        """
        return self['chantypes']

    @property
    def case_mapping(self) -> str:
        """
        Returns the case mapping.

        Example::

            >>> support.case_mapping
            'rfc1459'
        """
        return self['casemapping']

    #

    def is_channel(self, channel_name: str) -> bool:
        """
        Returns True if supplied channel name is a valid channel name.

        Example::

            >>> support.is_channel('#darkscience')
            True

            >>> support.is_channel('kylef')
            False
        """
        if ',' in channel_name or ' ' in channel_name:
            return False

        if len(channel_name) > self.maximum_channel_length:
            return False

        for prefix in self['chantypes']:
            if channel_name.startswith(prefix):
                return True

        return False

    @property
    def bot_mode(self) -> Optional[str]:
        """
        https://ircv3.net/specs/extensions/bot-mode
        """

        return self.get('BOT')
