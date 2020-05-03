import re
from typing import Optional


class Nick(object):
    IRC_USERHOST_REGEX = re.compile(r'^(.*)!(.*)@(.*)$')

    @classmethod
    def parse(cls, userhost):
        m = cls.IRC_USERHOST_REGEX.match(userhost)
        if m:
            return cls(m.group(1), m.group(2), m.group(3))
        return cls(host=userhost)

    def __init__(
        self, nick: str = '', ident: Optional[str] = '', host: Optional[str] = ''
    ):
        self.nick = nick
        self.ident = ident
        self.host = host

    def __str__(self):
        return self.nick

    def __repr__(self):
        return '<Nick %s!%s@%s>' % (self.nick, self.ident, self.host)

    def __eq__(self, other):
        if not isinstance(other, Nick):
            return False

        return (
            other.nick == self.nick
            and other.ident == self.ident
            and other.host == self.host
        )
