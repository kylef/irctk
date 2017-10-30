import re
import datetime
import string
import asyncio

from irctk.routing import *
from irctk.isupport import ISupport
from irctk.nick import Nick
from irctk.channel import Channel, Membership

IRC_CAP_REGEX = re.compile(r"^(\S+) (\S+) :(.+)$")
IRC_PRIVMSG_REGEX = re.compile(r"^(\S+) :(.+)$")
IRC_NAMES_REGEX = re.compile(r'^(@|=|\+) (\S+) :(.+)$')

IRC_KICK_REGEX = re.compile(r'^(\S+) (\S+) :(.+)$')


class IRCIgnoreLine(Exception):
    pass


class Client:
    channel_class = Channel
    nick_class = Nick

    def __init__(self, nickname='irctk', ident='irctk', realname='irctk', password=None):
        super(Client, self).__init__()

        self.nickname = nickname
        self.ident = ident
        self.realname = realname
        self.password = password

        self.is_connected = False
        self.is_registered = False
        self.secure = False
        self.read_until_data = "\r\n"
        self.nick = self.nick_class()

        self.channels = []
        self.isupport = ISupport()

        self.cap_accepted = []
        self.cap_pending = []

        self.resolver = RegexResolver(
            (r'^:(\S+) (\d{3}) ([\w*]+) :?(.+)$', self.handle_numerical),
            (r'^:(\S+) (\S+) (.+)$', self.handle_command),
            (r'^PING :?(.+)$', self.handle_ping)
        )

    async def connect(self, host, port, use_tls=False, loop=None):
        """
        Connect to the IRC server
        """

        self.secure = use_tls
        connection = asyncio.open_connection(host, port, ssl=use_tls, loop=loop)
        self.reader, self.writer = await connection

        self.is_connected = True
        self.authenticate()
        await self.writer.drain()

        while self.is_connected:
            raw_message = await self.reader.readline()

            if not raw_message:
                self.is_registered = False
                self.is_connected = False
                self.writer.close()

            self.read_data(raw_message.decode('utf-8'))
            await self.writer.drain()

    # Variables

    def get_nickname(self):
        return self.nickname

    def get_alt_nickname(self, nickname):
        return nickname + '_'

    def get_ident(self):
        return self.ident

    def get_realname(self):
        return self.realname

    def get_password(self):
        return self.password

    # CAP

    def supports_cap(self, cap):
        return cap in ['multi-prefix']

    # Support

    def irc_equal(self, lhs, rhs):
        """
        Determine if two strings are IRC equal.
        """

        if self.isupport.case_mapping == 'rfc1459':
            def lower(string):
                return (string.lower()
                    .replace('[', '{')
                    .replace(']', '}')
                    .replace('\\', '|'))
        elif self.isupport.case_mapping == 'rfc1459-strict':
            def lower(string):
                return (string.lower()
                    .replace('[', '{')
                    .replace(']', '}')
                    .replace('\\', '|')
                    .replace('^', '~'))
        elif self.isupport.case_mapping == 'ascii':
            lower = string.lower
        else:
            # Unknown case mapping
            lower = string.lower

        return lower(lhs) == lower(rhs)

    # Channels

    def is_channel(self, channel):
        if isinstance(channel, Channel):
            return True

        return self.isupport.is_channel(channel)

    def find_channel(self, name):
        for channel in self.channels:
            if self.irc_equal(channel.name, name):
                return channel

    def add_channel(self, name, key=None):
        channel = self.find_channel(name)

        if not channel:
            channel = self.channel_class(name)
            self.channels.append(channel)

        if key:
            channel.key = key

        return channel

    # Socket

    def quit(self, message='Disconnected'):
        """
        Disconnects from IRC and closes the connection. Accepts an optional
        reason.
        """
        self.send("QUIT", message)
        self.writer.close()

    def send_privmsg(self, target, message):
        """
        Sends a private message to a target.

        Example::

            >>> client.send_privmsg('kyle', 'Hi')
            >>> client.send_privmsg(channel, 'Hi')
        """

        self.send_line('PRIVMSG {} :{}'.format(target, message))

    def send_join(self, channel, key=None):
        """
        Sends a JOIN channel command.

            >>> client.send_join('#palaver')
        """

        if key:
            self.send_line('JOIN {} {}'.format(channel, key))
        else:
            self.send_line('JOIN {}'.format(channel))

    def send_part(self, channel):
        """
        Sends a PART channel command.

            >>> client.send_part('#palaver')
        """

        self.send_line('PART {}'.format(channel))

    def send_line(self, line):
        """
        Sends a raw line to IRC

        Example::

            >>> client.send_line('PRIVMSG kylef :Hey!')
        """
        self.writer.write('{}\r\n'.format(line).encode('utf-8'))

    def send(self, *args, **kwargs):
        force = kwargs.get('force', False)
        args = [str(arg) for arg in args]

        try:
            last = args[-1]
        except IndexError:
            return

        if force or last.startswith(':') or ' ' in last:
            args.append(':' + args.pop())

        self.send_line(' '.join(args))

    def authenticate(self):
        if not self.is_registered:
            self.send('CAP', 'LS')

            password = self.get_password()
            if password:
                self.send('PASS', password)

            self.send('NICK', self.get_nickname())
            self.send('USER', self.get_ident(), '0', '*', self.get_realname(), force=True)

    # Channel

    def channel_add_nick(self, channel, nick):
        self.channel_add_membership(channel, Membership(nick))

    def channel_add_membership(self, channel, membership):
        if self.channel_find_membership(channel, membership.nick):
            return

        if membership.nick == self.nick:
            channel.is_active = True

        channel.members.append(membership)

    def channel_remove_nick(self, channel, nick):
        membership = self.channel_find_membership(channel, nick)
        if membership:
            channel.members.remove(membership)

            if self.nick == membership.nick:
                channel.leave()

            return True

        return False

    def channel_find_membership(self, channel, nick):
        for membership in channel.members:
            if self.irc_equal(membership.nick.nick, str(nick)):
                return membership


    def channel_find_nick(self, channel, nick):
        membership = self.channel_find_membership(channel, nick)
        if membership:
            return membership.nick

    # Handle IRC lines

    def read_data(self, data):
        line = data.strip()

        try:
            self.irc_raw(line)
        except IRCIgnoreLine:
            return

        self.resolver(line)

    def handle_numerical(self, server, command, nick, args):
        numeric = int(command)
        if hasattr(self, 'handle_%s' % numeric):
            getattr(self, 'handle_%s' % numeric)(server, nick, args)

    def handle_command(self, sender, command, args):
        command = command.lower()
        nick = self.nick_class.parse(sender)

        if hasattr(self, 'handle_%s' % command):
            getattr(self, 'handle_%s' % command)(nick, args)

    def handle_1(self, server, nick, args):
        self.is_registered = True
        self.nick.nick = nick

        self.send('WHO', self.nick)
        self.irc_registered()

    def handle_5(self, server, nick, args):
        self.isupport.parse(args)

    def handle_324(self, server, nick, args): # MODE
        channel_name, mode_line = args.split(' ', 1)

        channel = self.find_channel(channel_name)
        if channel:
            channel.modes = {}
            channel.mode_change(mode_line, self.isupport)

    def handle_329(self, server, nick, args):
        channel_name, timestamp = args.split(' ', 1)

        channel = self.find_channel(channel_name)
        if channel:
            channel.creation_date = datetime.datetime.fromtimestamp(int(timestamp))

    def handle_332(self, server, nick, args):
        chan, topic = args.split(' ', 1)
        if topic.startswith(':'):
            topic = topic[1:]

        channel = self.find_channel(chan)
        if channel:
            channel.topic = topic

    def handle_333(self, server, nick, args):
        chan, owner, timestamp = args.split(' ', 2)

        channel = self.find_channel(chan)
        if channel:
            channel.topic_owner = owner
            channel.topic_date = datetime.datetime.fromtimestamp(int(timestamp))

    def handle_352(self, server, nick, args):
        args = args.split(' ')

        try:
            nick = args[4]
            ident = args[1]
            host = args[2]
        except IndexError:
            return

        if self.nick.nick == nick:
            self.nick.ident = ident
            self.nick.host = host

    def handle_432(self, server, nick, args):
        # Erroneous Nickname: Illegal characters
        self.handle_433(server, nick, args)

    def handle_433(self, server, nick, args):
        # Nickname is already in use
        if nick == '*':
            nick = self.get_nickname()

        if not self.is_registered:
            self.send('NICK', self.get_alt_nickname(nick))

    def names_353_to_membership(self, nick):
        for mode, prefix in self.isupport['prefix'].items():
            if nick.startswith(prefix):
                nickname = nick[len(mode):]
                if '@' in nickname:
                    n = self.nick_class.parse(nickname)
                else:
                    n = self.nick_class(nick=nickname)
                return Membership(n, [mode])
        if '@' in nick:
            return Membership(self.nick_class.parse(nick))
        return Membership(self.nick_class(nick=nick))

    def handle_353(self, server, nick, args):
        m = IRC_NAMES_REGEX.match(args)
        if m:
            channel = self.find_channel(m.group(2))
            if channel:
                users = m.group(3)

                for user in users.split():
                    membership = self.names_353_to_membership(user)
                    self.channel_add_membership(channel, membership)

    def handle_ping(self, line):
        self.send('PONG', line)

    def handle_cap(self, nick, line):
        m = IRC_CAP_REGEX.match(line)
        if m:
            command = m.group(2).lower()
            args = m.group(3)

            if command == "ls":
                supported_caps = args.lower().split()

                for cap in supported_caps:
                    if self.supports_cap(cap):
                        self.send('CAP', 'REQ', cap)
                        self.cap_pending.append(cap)
            elif command == "ack":
                caps = args.lower().split()

                for cap in caps:
                    if cap in self.cap_pending:
                        self.cap_pending.remove(cap)
                        self.cap_accepted.append(cap)
            elif command == "nak":
                supported_caps = args.lower().split()

                for cap in supported_caps:
                    if cap in self.cap_pending:
                        self.cap_pending.remove(args)

        if not self.cap_pending:
            self.send('CAP', 'END')

    def handle_join(self, nick, line):
        if line.startswith(':'):
            chan = line[1:]
        else:
            chan = line

        channel = self.find_channel(chan)

        if not channel and self.irc_equal(self.nick.nick, nick.nick):
            channel = self.add_channel(chan)

        if channel:
            self.channel_add_nick(channel, nick)
            self.irc_channel_join(nick, channel)

    def handle_part(self, nick, line):
        if ' :' in line:
            chan, message = line.split(' :', 1)
        else:
            chan = line
            message = ''

        channel = self.find_channel(chan)
        if channel:
            self.channel_remove_nick(channel, nick)
            self.irc_channel_part(nick, channel, message)

    def handle_kick(self, nick, line):
        m = IRC_KICK_REGEX.match(line)
        if m:
            chan = m.group(1)
            kicked_nick = m.group(2)
            kicked_nick = self.nick_class(nick=kicked_nick)
            message = m.group(3)

            channel = self.find_channel(chan)
            if channel:
                self.channel_remove_nick(channel, kicked_nick)
                self.irc_channel_kick(nick, channel, message)

    def handle_topic(self, nick, line):
        chan, topic = line.split(' ', 1)
        if topic.startswith(':'):
            topic = topic[1:]

        channel = self.find_channel(chan)
        if channel:
            channel.topic = topic
            channel.topic_owner = nick
            channel.topic_date = datetime.datetime.now()

            self.irc_channel_topic(nick, channel)

    def handle_nick(self, nick, new_nick):
        if self.irc_equal(self.nick.nick, nick.nick):
            self.nick.nick = new_nick

        for channel in self.channels:
            for membership in channel.members:
                if self.irc_equal(membership.nick.nick, nick.nick):
                    membership.nick.nick = new_nick

    def handle_privmsg(self, nick, line):
        m = IRC_PRIVMSG_REGEX.match(line)
        if m:
            message = m.group(2)
            if m.group(1) == str(self.nick):
                self.irc_private_message(nick, message)
            else:
                channel = self.find_channel(m.group(1))
                if channel:
                    self.irc_channel_message(self.channel_find_nick(channel, nick.nick), channel, message)

    def handle_mode(self, nick, line):
        subject, mode_line = line.split(' ', 1)

        if self.is_channel(subject):
            channel = self.find_channel(subject)

            if channel:
                channel.mode_change(mode_line, self.isupport)

    def handle_quit(self, nick, reason):
        for channel in self.channels:
            if self.channel_remove_nick(channel, nick):
                self.irc_channel_quit(nick, channel, reason)

    # Delegation methods

    def irc_registered(self):
        if hasattr(self.delegate, 'irc_registered'):
            self.delegate.irc_registered(self)

    def irc_raw(self, line):
        if hasattr(self.delegate, 'irc_raw'):
            self.delegate.irc_raw(self, line)

    def irc_private_message(self, nick, message):
        if hasattr(self.delegate, 'irc_private_message'):
            self.delegate.irc_private_message(self, nick, message)

    def irc_channel_message(self, nick, channel, message):
        if hasattr(self.delegate, 'irc_channel_message'):
            self.delegate.irc_channel_message(self, nick, channel, message)

    def irc_channel_join(self, nick, channel):
        if hasattr(self.delegate, 'irc_channel_join'):
            self.delegate.irc_channel_join(self, nick, channel)

    def irc_channel_quit(self, nick, channel, message):
        if hasattr(self.delegate, 'irc_channel_quit'):
            self.delegate.irc_channel_quit(self, nick, channel, message)

    def irc_channel_part(self, nick, channel, message):
        if hasattr(self.delegate, 'irc_channel_part'):
            self.delegate.irc_channel_part(self, nick, channel, message)

    def irc_channel_kick(self, nick, channel, message):
        if hasattr(self.delegate, 'irc_channel_kick'):
            self.delegate.irc_channel_kick(self, nick, channel, message)

    def irc_channel_topic(self, nick, channel):
        if hasattr(self.delegate, 'irc_channel_topic'):
            self.delegate.irc_channel_topic(self, nick, channel)

    def irc_channel_mode(self, nick, channel, mode, arg, added):
        pass

