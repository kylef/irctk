from typing import List, Optional


class MessageTag:
    @classmethod
    def parse_value(cls, value: str) -> str:
        return (
            value.replace('\\:', ';')
            .replace('\\s', ' ')
            .replace('\\\\', '\\')
            .replace('\\r', '\r')
            .replace('\\n', '\n')
        )

    @classmethod
    def parse(cls, string: str):
        if string.startswith('+'):
            # FIXME support client tags
            string = string[1:]

        vendor = None
        value = None

        if '=' in string:
            string, value = string.split('=', 1)
            value = cls.parse_value(value)

        if '/' in string:
            vendor, string = string.split('/', 1)

        return cls(vendor=vendor, name=string, value=value)

    def __init__(self, vendor: str = None, name: str = None, value: str = None):
        self.vendor = vendor
        self.name = name
        self.value = value

    def __str__(self):
        tag = ''

        # FIXMEif client_only prepend +

        if self.vendor:
            tag += self.vendor + '/'

        tag += self.name

        if self.value and len(self.value) > 0:
            tag += '=' + (
                self.value.replace('\\', '\\\\')
                .replace(';', '\\:')
                .replace(' ', '\\s')
                .replace('\r', '\\r')
                .replace('\n', '\\n')
            )

        return tag


class Message:
    @classmethod
    def parse(cls, string: str):
        """
        Parse an IRC line into a Message instance

        >>> message = Message.parse(':doe!doe@example.com PRIVMSG #example :Hello World')
        >>> message.prefix
        'doe!doe@example.com'
        >>> message.command
        'PRIVMSG'
        >>> message.parameters
        ['#example', 'Hello World']
        """

        tags = []
        prefix = None
        parameters = []

        if string.startswith('@'):
            tags_str, string = string[1:].split(' ', 1)
            tags = list(map(MessageTag.parse, tags_str.split(';')))

        if string.startswith(':'):
            prefix, string = string.split(' ', 1)
            prefix = prefix[1:]

        if ' ' in string:
            command, string = string.split(' ', 1)
        else:
            command = string
            string = ''

        while len(string) != 0:
            if string[0] == ':':
                parameters.append(string[1:])
                string = ''
            elif ' ' in string:
                parameter, string = string.split(' ', 1)
                parameters.append(parameter)
            else:
                parameters.append(string)
                string = ''

        return cls(tags, prefix, command, parameters)

    def __init__(
        self,
        tags: List[MessageTag] = None,
        prefix: str = None,
        command: str = '',
        parameters: List[str] = None,
    ):
        self.tags = tags or []
        self.prefix = prefix
        self.command = command
        self.parameters = parameters or []
        self.colon = False

    def __str__(self):
        """
        Converts a Message instance into a string

        >>> message = Message(command='CAP', parameters=['LS'])
        >>> str(message)
        'CAP LS'
        """
        string = ''

        if len(self.tags) > 0:
            string += '@' + ';'.join(map(str, self.tags))

        if self.prefix:
            if len(string) > 0:
                string += ' '

            string += ':' + self.prefix

        if len(self.command) > 0:
            if len(string) > 0:
                string += ' '

            string += self.command

        if len(self.parameters) > 0:
            if len(string) > 0:
                string += ' '

            def parameter_to_string(item):
                index = item[0]
                parameter = item[1]

                if index + 1 == len(self.parameters) and (
                    self.colon
                    or len(parameter) == 0
                    or ' ' in parameter
                    or parameter.startswith(':')
                ):
                    return ':' + parameter
                return parameter

            string += ' '.join(map(parameter_to_string, enumerate(self.parameters)))

        return string

    def __bytes__(self):
        return str(self).encode('utf-8') + b'\r\n'

    def get(self, index: int) -> Optional[str]:
        """
        Returns a parameter at index or None

        >>> message = Message.parse('JOIN #example')
        >>> message.get(0)
        '#example'
        >>> message.get(1)
        """

        if index >= len(self.parameters):
            return None

        return self.parameters[index]
