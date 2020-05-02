from typing import List


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

        if string.startswith(':'):
            prefix, string = string.split(' ', 1)
            prefix = prefix[1:]
        else:
            prefix = None

        command, string = string.split(' ', 1)
        parameters = []

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

        return cls(prefix, command, parameters)

    def __init__(self, prefix: str = None, command: str = '', parameters: List[str] = None):
        self.prefix = prefix
        self.command = command
        self.parameters = parameters or []

    def __str__(self):
        """
        Converts a Message instance into a string

        >>> message = Message(command='CAP', parameters=['LS'])
        >>> str(message)
        'CAP LS'
        """
        string = ''

        if self.prefix:
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

                if index + 1 == len(self.parameters) and (len(parameter) == 0 or ' ' in parameter or parameter.startswith(':')):
                    return ':' + parameter
                return parameter

            string += ' '.join(map(parameter_to_string, enumerate(self.parameters)))

        return string
