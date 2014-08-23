import re

class RegexPattern(object):
    def __init__(self, regex, handler, default_kwargs={}):
        self.regex = re.compile(regex, re.UNICODE)
        self.callback = handler
        self.default_kwargs = default_kwargs

    def resolve(self, line):
        match = self.regex.search(line)
        if match:
            return self.match_found(line, match)

    def match_found(self, line, match):
        kwargs = match.groupdict()

        if kwargs:
            args = tuple()
        else:
            args = match.groups()

        kwargs.update(self.default_kwargs)

        return self.callback, args, kwargs

class RegexResolver(object):
    def __init__(self, *patterns):
        self.patterns = []

        for pattern in patterns:
            if isinstance(pattern, (list, tuple)):
                pattern = RegexPattern(*pattern)

            self.patterns.append(pattern)

    def resolve(self, line):
        for pattern in self.patterns:
            result = pattern.resolve(line)
            if result is not None:
                return result
        return

    def __call__(self, line):
        result = self.resolve(line)
        if result:
            callback, args, kwargs = result
            return callback(*args, **kwargs)

