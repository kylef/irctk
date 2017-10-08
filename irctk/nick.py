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

    def __str__(self):
        return self.nick

    def __repr__(self):
        return '<Nick %s!%s@%s>' % (self.nick, self.ident, self.host)

    def __eq__(self, other):
        return self.client.irc_equal(str(other), self.nick)

    @property
    def channels(self):
        """
        Returns all the Channels that both the nick and the client has joined.
        """
        return [channel for channel in self.client.channels if channel.has_nick(self)]

    def update(self):
        if self == self.client.nick:
            self.client.nick.ident = self.ident
            self.client.nick.host = self.host

        for channel in self.client.channels:
            n = channel.find_nick(self)
            if n:
                n.ident = self.ident
                n.host = self.host

