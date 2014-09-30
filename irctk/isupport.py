import re


class ISupport(dict):
    IRC_ISUPPORT_PREFIX = re.compile(r'^\((.+)\)(.+)$')

    def __init__(self):
        self['casemapping'] = 'rfc1459'
        self['chanmodes'] = {
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
        }

        self['prefix'] = { 'o': '@', 'v': '+' }
        self['channellen'] = 200
        self['chantypes'] = ['#', '&']
        self['modes'] = 3
        self['nicklen'] = 9

        # Unlimited
        self['topiclen'] = 0
        self['kicklen'] = 0
        self['modes'] = 0

    def __str__(self):
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

    def to_str_chanmodes(self):
        chanmodes = self.get('chanmodes', {})
        list_args, arg, arg_set, no_args = [], [], [], []

        for mode in chanmodes:
            value = chanmodes[mode]

            if value is list:
                list_args.append(mode)
            elif value is 'arg':
                arg.append(mode)
            elif value is 'arg_set':
                arg_set.append(mode)
            elif value is None:
                no_args.append(mode)

        return ','.join(map(lambda modes: ''.join(modes), [list_args, arg, arg_set, no_args]))

    def to_str_prefix(self):
        prefix = self.get('prefix', {})

        modes = ''
        prefixes = ''

        for mode in prefix:
            modes += mode
            prefixes += prefix[mode]

        return '({}){}'.format(modes, prefixes)

    # Parsing

    def parse(self, line):
        for pair in line.split():
            if '=' not in pair:
                self[pair] = None
                continue

            key, value = pair.split('=', 1)

            if key == 'PREFIX':
                self.parse_prefix(value)
            elif key == 'CHANMODES':
                self.parse_chanmodes(value)
            elif key == 'CHANTYPES':
                self['chantypes'] = list(value)
            elif key in ('CHANNELLEN', 'NICKLEN', 'MODES', 'TOPICLEN', 'KICKLEN', 'MODES'):
                self[key.lower()] = int(value)
            elif key == 'CASEMAPPING':
                self[key.lower()] = value

    def parse_prefix(self, value):
        self['prefix'] = {}

        m = self.IRC_ISUPPORT_PREFIX.match(value)
        if m and len(m.group(1)) == len(m.group(2)):
            for x in range(0, len(m.group(1))):
                self['prefix'][m.group(1)[x]] = m.group(2)[x]

    def parse_chanmodes(self, value):
        try:
            list_args, arg, arg_set, no_args = value.split(',')
        except:
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
    def maximum_nick_length(self):
        """
        Returns the maximum length of a nickname.

        Example::

            >>> support.maximum_nick_length
            9
        """
        return self['nicklen']

    @property
    def maximum_channel_length(self):
        """
        Returns the maximum length of a channel name.

        Example::

            >>> support.maximum_channel_length
            200
        """
        return self['channellen']

    @property
    def channel_prefixes(self):
        """
        Returns a list of channel prefixes.

        Example::

            >>> support.channel_prefixes
            ['#', '&']
        """
        return self['chantypes']

    #

    def is_channel(self, channel_name):
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

