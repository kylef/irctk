from typing import List


class Message:
    @classmethod
    def parse(cls, string: str):
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

        return cls(command, parameters)

    def __init__(self, command: str, parameters: List[str] = None):
        self.command = command
        self.parameters = parameters or []

    def __str__(self):
        string = ''

        if len(self.command) > 0:
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
