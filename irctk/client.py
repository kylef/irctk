import re
import datetime

from zokket.tcp import TCPSocket

from irctk.routing import *
from irctk.isupport import ISupport
from irctk.nick import Nick
from irctk.channel import Channel

IRC_CAP_REGEX = re.compile(r"^(\S+) (\S+) :(.+)$")
IRC_PRIVMSG_REGEX = re.compile(r"^(\S+) :(.+)$")
IRC_NAMES_REGEX = re.compile(r'^(@|=|\+) (\S+) :(.+)$')

IRC_KICK_REGEX = re.compile(r'^(\S+) (\S+) :(.+)$')


class IRCIgnoreLine(Exception):
    pass


class Client(TCPSocket):
    channel_class = Channel
    nick_class = Nick

    def __init__(self, nickname='irctk', ident='irctk', realname='irctk', password=None):
        super(Client, self).__init__()

        self.nickname = nickname
        self.ident = ident
        self.realname = realname
        self.password = password

        self.is_registered = False
        self.secure = False
        self.read_until_data = "\r\n"
        self.nick = self.nick_class(self)

        self.channels = []
        self.isupport = ISupport()

        self.cap_accepted = []
        self.cap_pending = []

        self.resolver = RegexResolver(
            (r'^:(\S+) (\d{3}) ([\w*]+) (.+)$', self.handle_numerical),
            (r'^:(\S+) (\S+) (.+)$', self.handle_command),
            (r'^PING :?(.+)$', self.handle_ping)
        )

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
        return cap in []

    # Channels

    def is_channel(self, channel):
        if isinstance(channel, Channel):
            return True

        return self.isupport.is_channel(channel)

    def find_channel(self, name):
        for channel in self.channels:
            if channel.name == name:
                return channel

    def add_channel(self, name, key=None):
        channel = self.find_channel(name)

        if not channel:
            channel = self.channel_class(self, name)
            self.channels.append(channel)

        if key:
            channel.key = key

        return channel

    # Socket

    def connect(self, host, port, secure=False):
        self.secure = secure
        super(Client, self).connect(host, port, timeout=10)

    def socket_did_connect(self):
        if self.secure:
            self.start_tls()
        else:
            self.authenticate()

    def socket_did_secure(self):
        self.authenticate()

    def socket_did_disconnect(self, err=None):
        super(Client, self).socket_did_disconnect(err)
        self.is_registered = False

    def quit(self, message='Disconnected'):
        self.send("QUIT", message)
        self.close()

    def send_line(self, line):
        super(Client, self).send(line + "\r\n")

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
        nick = self.nick_class.parse(self, sender)

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
            channel.mode_change(mode_line)

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

    def names_353_to_nick(self, nick):
        for mode, prefix in self.isupport['prefix'].iteritems():
            if nick.startswith(prefix):
                n = self.nick_class(self, nick=nick[len(mode):])
                n.add_perm(mode)
                return n
        return self.nick_class(self, nick=nick)

    def handle_353(self, server, nick, args):
        m = IRC_NAMES_REGEX.match(args)
        if m:
            channel = self.find_channel(m.group(2))
            if channel:
                users = m.group(3)

                for user in users.split():
                    nick = self.names_353_to_nick(user)
                    channel.add_nick(nick)

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
        if channel:
            channel.add_nick(nick)
            self.irc_channel_join(nick, channel)

    def handle_part(self, nick, line):
        if ' :' in line:
            chan, message = args.split(' :', 1)
        else:
            chan = line
            message = ''

        channel = self.find_channel(chan)
        if channel:
            channel.remove_nick(nick)
            self.irc_channel_part(nick, channel, message)

    def handle_kick(self, nick, line):
        m = IRC_KICK_REGEX.match(line)
        if m:
            chan = m.group(1)
            kicked_nick = m.group(2)
            kicked_nick = self.nick_class(self, nick=kicked_nick)
            message = m.group(3)

            channel = self.find_channel(chan)
            if channel:
                channel.remove_nick(kicked_nick)
                self.irc_channel_kick(nick, channel, message)

    def handle_topic(self, nick, line):
        chan, topic = args.split(' ', 1)
        if topic.startswith(':'):
            topic = topic[1:]

        channel = self.find_channel(chan)
        if channel:
            channel.topic = topic
            channel.topic_owner = nick
            channel.topic_date = datetime.datetime.now()

            self.irc_channel_topic(nick, channel)

    def handle_nick(self, nick, new_nick):
        nick.set_nick(new_nick)

    def handle_privmsg(self, nick, line):
        m = IRC_PRIVMSG_REGEX.match(line)
        if m:
            message = m.group(2)
            if m.group(1) == str(self.nick):
                self.irc_private_message(nick, message)
            else:
                channel = self.find_channel(m.group(1))
                if channel:
                    self.irc_channel_message(channel.find_nick(nick), channel, message)

    def handle_mode(self, nick, line):
        subject, mode_line = line.split(' ', 1)

        if self.is_channel(subject):
            channel = self.find_channel(subject)

            if channel:
                channel.mode_change(mode_line)

    def handle_quit(self, nick, reason):
        for channel in nick.channels:
            self.irc_channel_quit(nick, channel, reason)
            channel.remove_nick(nick)

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

