import re


class Nick(object):
    IRC_USERHOST_REGEX = re.compile(r'^(.*)!(.*)@(.*)$')

    @classmethod
    def parse(cls, client, userhost):
        m = cls.IRC_USERHOST_REGEX.match(userhost)
        if m:
            return cls(client, m.group(1), m.group(2), m.group(3))
        return cls(client, host=userhost)

    def __init__(self, client, nick='', ident='', host=''):
        self.client = client
        self.nick = nick
        self.ident = ident
        self.host = host

        self.channel_modes = []

    def __str__(self):
        return self.nick

    def __repr__(self):
        return '<Nick %s!%s@%s>' % (self.nick, self.ident, self.host)

    def __eq__(self, other):
        return str(other) == self.nick

    def send(self, message):
        self.client.send('PRIVMSG', self, message, force=True)

    @property
    def channels(self):
        return [channel for channel in self.client.channels if channel.has_nick(self)]

    # Channel

    def has_perm(self, perm):
        return perm in self.channel_modes

    def add_perm(self, perm):
        if not self.has_perm(perm):
            self.channel_modes.append(perm)

    def remove_perm(self, perm):
        self.channel_modes.remove(perm)

    def set_nick(self, nick):
        if self == self.client.nick:
            self.client.nick.nick = nick

        for channel in self.client.channels:
            n = channel.find_nick(self)
            if n:
                n.nick = nick

        self.nick = nick

    def update(self):
        if self == self.client.nick:
            self.client.nick.ident = self.ident
            self.client.nick.host = self.host

        for channel in self.client.channels:
            n = channel.find_nick(self)
            if n:
                n.ident = self.ident
                n.host = self.host

