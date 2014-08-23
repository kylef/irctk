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
        self['statusmsg'] = []
        self['std'] = []
        self['targmax'] = {}
        self['excepts'] = False
        self['idchan'] = {}
        self['invex'] = False
        self['maxlist'] = {}
        self['network'] = None
        self['safelist'] = False
        self['statusmsg'] = []

        # Unlimited
        self['topiclen'] = 0
        self['kicklen'] = 0
        self['modes'] = 0

    def parse(self, line):
        for pair in line.split():
            if '=' not in pair:
                continue

            key, value = pair.split('=', 1)

            if key == 'PREFIX':
                self.parse_prefix(value)
            elif key == 'CHANMODES':
                self.parse_chanmodes(value)
            elif key == 'CHANTYPES':
                self['chantypes'] = list(value)
            elif key == 'CHANNELLEN' or key == 'NICKLEN':
                self[key.lower()] = int(value)

    def parse_prefix(self, value):
        m = self.IRC_ISUPPORT_PREFIX.match(value)
        if m and len(m.group(1)) == len(m.group(2)):
            for x in range(0, len(m.group(1))):
                self['prefix'][m.group(1)[x]] = m.group(2)[x]

    def parse_chanmodes(self, value):
        try:
            list_args, arg, arg_set, no_args = value.split(',')
        except:
            return

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
        return self['nicklen']

    @property
    def maximum_channel_length(self):
        return self['channellen']

    @property
    def channel_prefixes(self):
        return self['chantypes']

    #

    def is_channel(self, channel_name):
        """
        Returns True if supplied channel name is a valid channel name.
        """
        if ',' in channel_name or ' ' in channel_name:
            return False

        if len(channel_name) > self.maximum_channel_length:
            return False

        for prefix in self['chantypes']:
            if channel_name.startswith(prefix):
                return True

        return False

