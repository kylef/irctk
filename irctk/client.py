from typing import List, Optional
import datetime
import string
import asyncio
import logging

from irctk.isupport import ISupport
from irctk.nick import Nick
from irctk.channel import Channel, Membership
from irctk.message import Message


class IRCIgnoreLine(Exception):
    pass


class Client:
    channel_class = Channel
    nick_class = Nick

    def __init__(
        self,
        nickname: str = 'irctk',
        ident: str = 'irctk',
        realname: str = 'irctk',
        password: str = None,
    ):
        super(Client, self).__init__()

        self.logger = logging.getLogger(__name__)

        self.nickname = nickname
        self.ident = ident
        self.realname = realname
        self.password = password

        self.is_connected = False
        self.is_registered = False
        self.secure = False
        self.read_until_data = "\r\n"
        self.nick = self.nick_class()

        self.channels: List[Channel] = []
        self.isupport = ISupport()

        self.cap_accepted: List[str] = []
        self.cap_pending: List[str] = []

        self.modules: List = []

    async def connect(self, host: str, port: int, use_tls: bool = False, loop=None):
        """
        Connect to the IRC server
        """

        self.logger.info('Connecting to {}:{}'.format(host, port))

        self.secure = use_tls
        connection = asyncio.open_connection(host, port, ssl=use_tls, loop=loop)
        try:
            self.reader, self.writer = await connection
        except Exception as exception:
            self.logger.error('Disconnected', exception)
            self.irc_disconnected(exception)
            return

        self.is_connected = True
        self.authenticate()
        await self.writer.drain()

        while self.is_connected:
            raw_message = await self.reader.readline()

            if not raw_message:
                self.is_registered = False
                self.is_connected = False
                self.writer.close()
                self.irc_disconnected(None)
                self.logger.info('Disconnected')
                return

            self.read_data(raw_message.decode('utf-8'))
            await self.writer.drain()

    # Variables

    def get_nickname(self) -> str:
        return self.nickname

    def get_alt_nickname(self) -> str:
        return self.nickname + '_'

    def get_ident(self) -> str:
        return self.ident

    def get_realname(self) -> str:
        return self.realname

    def get_password(self) -> Optional[str]:
        return self.password

    # CAP

    def supports_cap(self, cap: str) -> bool:
        return cap in ['multi-prefix']

    # Support

    def irc_equal(self, lhs: str, rhs: str) -> bool:
        """
        Determine if two strings are IRC equal.
        """

        if self.isupport.case_mapping == 'rfc1459':

            def lower(value: str):
                return (
                    value.lower().replace('[', '{').replace(']', '}').replace('\\', '|')
                )

        elif self.isupport.case_mapping == 'rfc1459-strict':

            def lower(value: str):
                return (
                    value.lower()
                    .replace('[', '{')
                    .replace(']', '}')
                    .replace('\\', '|')
                    .replace('^', '~')
                )

        elif self.isupport.case_mapping == 'ascii':

            def lower(value: str):
                return value.lower()

        else:
            # Unknown case mapping
            def lower(value: str):
                return value.lower()

        return lower(lhs) == lower(rhs)

    # Channels

    def is_channel(self, channel) -> bool:
        if isinstance(channel, Channel):
            return True

        return self.isupport.is_channel(channel)

    def find_channel(self, name) -> Optional[Channel]:
        for channel in self.channels:
            if self.irc_equal(channel.name, name):
                return channel

        return None

    def add_channel(self, name: str, key: str = None) -> Channel:
        channel = self.find_channel(name)

        if not channel:
            channel = self.channel_class(name)
            self.channels.append(channel)

        if key:
            channel.key = key

        return channel

    # Socket

    def quit(self, message: str = 'Disconnected'):
        """
        Disconnects from IRC and closes the connection. Accepts an optional
        reason.
        """
        self.send("QUIT", message)
        self.writer.close()

    def send_privmsg(self, target, message: str):
        """
        Sends a private message to a target.

        Example::

            >>> client.send_privmsg('kyle', 'Hi')
            >>> client.send_privmsg(channel, 'Hi')
        """

        self.send_line('PRIVMSG {} :{}'.format(target, message))

    def send_join(self, channel, key: str = None):
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

    def send_line(self, line: str):
        """
        Sends a raw line to IRC

        Example::

            >>> client.send_line('PRIVMSG kylef :Hey!')
        """
        self.logger.debug('C: {}'.format(line))
        self.writer.write('{}\r\n'.format(line).encode('utf-8'))

    def send(self, message_or_command, *parameters, colon: bool = False):
        if isinstance(message_or_command, Message):
            message = message_or_command
            if len(parameters) != 0 or colon:
                raise TypeError(
                    'send() takes 1 positional arguments but {} was given'.format(
                        len(parameters)
                    )
                )
        else:
            message = Message(
                command=message_or_command, parameters=list(map(str, parameters))
            )
            message.colon = colon

        self.send_line(str(message))

    def authenticate(self):
        if not self.is_registered:
            self.send('CAP', 'LS')

            password = self.get_password()
            if password:
                self.send('PASS', password)

            self.send('NICK', self.get_nickname())
            self.send(
                'USER', self.get_ident(), '0', '*', self.get_realname(), colon=True
            )

    # Channel

    def channel_add_nick(self, channel, nick):
        self.channel_add_membership(channel, Membership(nick))

    def channel_add_membership(self, channel, membership):
        if self.channel_find_membership(channel, membership.nick):
            return

        if self.irc_equal(membership.nick.nick, self.nick.nick):
            channel.is_attached = True

        channel.members.append(membership)

    def channel_remove_nick(self, channel, nick):
        membership = self.channel_find_membership(channel, nick)
        if membership:
            channel.members.remove(membership)

            if self.irc_equal(self.nick.nick, membership.nick.nick):
                channel.leave()

            return True

        return False

    def channel_find_membership(self, channel, nick):
        for membership in channel.members:
            if self.irc_equal(membership.nick.nick, str(nick)):
                return membership

    # Handle IRC lines

    def read_data(self, data: str):
        line = data.strip()
        self.logger.debug('S: {}'.format(line))

        try:
            self.irc_raw(line)
        except IRCIgnoreLine:
            return

        message = Message.parse(line)
        self.irc_message(message)

        command = message.command.lower()
        if hasattr(self, 'handle_{}'.format(command)):
            func = getattr(self, 'handle_{}'.format(command))
            func(message)

    def handle_001(self, message: Message):
        self.is_registered = True
        self.nick.nick = message.parameters[0]

        self.send('WHO', self.nick)
        self.irc_registered()

    def handle_005(self, message: Message):
        self.isupport.parse(message.parameters[1])

    def handle_324(self, message: Message):  # MODE
        channel = self.find_channel(message.get(1))
        if channel:
            channel.modes = {}
            channel.mode_change(' '.join(message.parameters[2:]), self.isupport)

    def handle_329(self, message: Message):
        channel = self.find_channel(message.get(1))
        timestamp = message.get(2)
        if channel and timestamp:
            channel.creation_date = datetime.datetime.fromtimestamp(int(timestamp))

    def handle_332(self, message: Message):
        channel = self.find_channel(message.get(1))
        if channel:
            channel.topic = message.get(2)

    def handle_333(self, message: Message):
        channel = self.find_channel(message.get(1))
        if channel:
            channel.topic_owner = message.get(2)

            topic_date = message.get(3)
            if topic_date:
                channel.topic_date = datetime.datetime.fromtimestamp(int(topic_date))

    # RPL_WHOREPLY
    def handle_352(self, message: Message):
        nick = message.get(5)

        if self.nick.nick == nick:
            self.nick.ident = message.get(2)
            self.nick.host = message.get(3)

    def handle_432(self, message: Message):
        # Erroneous Nickname: Illegal characters
        self.handle_433(message)

    def handle_433(self, message: Message):
        # Nickname is already in use
        if not self.is_registered:
            self.send('NICK', self.get_alt_nickname())

    def names_353_to_membership(self, nick):
        for mode, prefix in self.isupport['prefix'].items():
            if nick.startswith(prefix):
                nickname = nick[len(mode) :]
                if '@' in nickname:
                    n = self.nick_class.parse(nickname)
                else:
                    n = self.nick_class(nick=nickname)
                return Membership(n, [mode])
        if '@' in nick:
            return Membership(self.nick_class.parse(nick))
        return Membership(self.nick_class(nick=nick))

    def handle_353(self, message: Message):
        channel = self.find_channel(message.get(2))
        users = message.get(3)
        if channel and users:
            for user in users.split():
                membership = self.names_353_to_membership(user)
                self.channel_add_membership(channel, membership)

    def handle_ping(self, message: Message):
        self.send('PONG', ' '.join(message.parameters))

    def handle_cap(self, message: Message):
        command = message.get(1)
        param2 = message.get(2)
        if not param2:
            return

        if command == 'LS':
            supported_caps = param2.split()

            for cap in supported_caps:
                if self.supports_cap(cap):
                    self.send('CAP', 'REQ', cap)
                    self.cap_pending.append(cap)
        elif command == 'ACK':
            caps = param2.split()

            for cap in caps:
                if cap in self.cap_pending:
                    self.cap_pending.remove(cap)
                    self.cap_accepted.append(cap)
        elif command == 'NAK':
            supported_caps = param2.split()

            for cap in supported_caps:
                if cap in self.cap_pending:
                    self.cap_pending.remove(cap)

        if not self.cap_pending:
            self.send('CAP', 'END')

    def handle_join(self, message: Message):
        channel_name = message.get(0)
        if not channel_name:
            return

        nick = self.nick_class.parse(message.prefix)
        channel = self.find_channel(channel_name)

        if not channel and self.irc_equal(self.nick.nick, nick.nick):
            channel = self.add_channel(channel_name)

        if channel:
            self.channel_add_nick(channel, nick)
            self.irc_channel_join(nick, channel)

    def handle_part(self, message: Message):
        channel = self.find_channel(message.get(0))
        if channel:
            nick = self.nick_class.parse(message.prefix)
            reason = message.get(1)

            self.channel_remove_nick(channel, nick)
            self.irc_channel_part(nick, channel, reason)

    def handle_kick(self, message: Message):
        channel = self.find_channel(message.get(0))
        kicked_nickname = message.get(1)
        if channel and kicked_nickname:
            kicked_nick = self.nick_class(nick=kicked_nickname)
            reason = message.get(2)

            nick = self.nick_class.parse(message.prefix)
            self.channel_remove_nick(channel, kicked_nick)
            self.irc_channel_kick(nick, channel, reason)

    def handle_topic(self, message: Message):
        channel = self.find_channel(message.get(0))
        if channel:
            nick = self.nick_class.parse(message.prefix)
            channel.topic = message.get(1)
            channel.topic_owner = nick
            channel.topic_date = datetime.datetime.now()

            self.irc_channel_topic(nick, channel)

    def handle_nick(self, message: Message):
        nick = self.nick_class.parse(message.prefix)
        new_nick = message.get(0)

        if new_nick and self.irc_equal(self.nick.nick, nick.nick):
            self.nick.nick = new_nick

        for channel in self.channels:
            for membership in channel.members:
                if self.irc_equal(membership.nick.nick, nick.nick):
                    membership.nick.nick = new_nick

    def handle_privmsg(self, message: Message):
        sender = self.nick_class.parse(message.prefix)
        target = message.get(0)
        text = message.get(1)
        if not text:
            return

        if target == str(self.nick):
            self.irc_private_message(sender, text)
        else:
            channel = self.find_channel(target)
            if channel:
                self.irc_channel_message(sender, channel, text)

    def handle_mode(self, message: Message):
        subject = message.get(0)
        mode_line = ' '.join(message.parameters[1:])

        if self.is_channel(subject):
            channel = self.find_channel(subject)

            if channel:
                channel.mode_change(mode_line, self.isupport)

    def handle_quit(self, message: Message):
        nick = self.nick_class.parse(message.prefix)
        reason = message.get(0)

        for channel in self.channels:
            if self.channel_remove_nick(channel, nick):
                self.irc_channel_quit(nick, channel, reason)

    # Delegation methods

    @property
    def delegate(self):
        for module in self.modules:
            if isinstance(module, DelegateModule):
                return module.delegate

    @delegate.setter
    def delegate(self, delegate):
        for module in self.modules:
            if isinstance(module, DelegateModule):
                module.delegate = delegate
                return

        self.modules.append(DelegateModule(delegate))

    def irc_disconnected(self, error: Optional[Exception]):
        for module in self.modules:
            if hasattr(module, 'irc_disconnected'):
                module.irc_disconnected(self, error)

    def irc_registered(self):
        for module in self.modules:
            if hasattr(module, 'irc_registered'):
                module.irc_registered(self)

    def irc_raw(self, line: str):
        for module in self.modules:
            if hasattr(module, 'irc_raw'):
                module.irc_raw(self, line)

    def irc_message(self, message: Message):
        for module in self.modules:
            if hasattr(module, 'irc_message'):
                module.irc_message(self, message)

    def irc_private_message(self, nick: Nick, message: str):
        for module in self.modules:
            if hasattr(module, 'irc_private_message'):
                module.irc_private_message(self, nick, message)

    def irc_channel_message(self, nick: Nick, channel: Channel, message: str):
        for module in self.modules:
            if hasattr(module, 'irc_channel_message'):
                module.irc_channel_message(self, nick, channel, message)

    def irc_channel_join(self, nick: Nick, channel: Channel):
        for module in self.modules:
            if hasattr(module, 'irc_channel_join'):
                module.irc_channel_join(self, nick, channel)

    def irc_channel_quit(self, nick: Nick, channel: Channel, message: Optional[str]):
        for module in self.modules:
            if hasattr(module, 'irc_channel_quit'):
                module.irc_channel_quit(self, nick, channel, message)

    def irc_channel_part(self, nick: Nick, channel: Channel, message: Optional[str]):
        for module in self.modules:
            if hasattr(module, 'irc_channel_part'):
                module.irc_channel_part(self, nick, channel, message)

    def irc_channel_kick(self, nick: Nick, channel: Channel, message: Optional[str]):
        for module in self.modules:
            if hasattr(module, 'irc_channel_kick'):
                module.irc_channel_kick(self, nick, channel, message)

    def irc_channel_topic(self, nick: Nick, channel: Channel):
        for module in self.modules:
            if hasattr(module, 'irc_channel_topic'):
                module.irc_channel_topic(self, nick, channel)


class DelegateModule:
    def __init__(self, delegate):
        self.delegate = delegate

    def irc_disconnected(self, client: Client, error: Optional[Exception]):
        if hasattr(self.delegate, 'irc_disconnected'):
            self.delegate.irc_disconnected(client, error)

    def irc_registered(self, client: Client):
        if hasattr(self.delegate, 'irc_registered'):
            self.delegate.irc_registered(client)

    def irc_raw(self, client: Client, line: str):
        if hasattr(self.delegate, 'irc_raw'):
            self.delegate.irc_raw(client, line)

    def irc_message(self, client: Client, message: Message):
        if hasattr(self.delegate, 'irc_message'):
            self.delegate.irc_message(client, message)

    def irc_private_message(self, client: Client, nick: Nick, message: str):
        if hasattr(self.delegate, 'irc_private_message'):
            self.delegate.irc_private_message(client, nick, message)

    def irc_channel_message(
        self, client: Client, nick: Nick, channel: Channel, message: str
    ):
        if hasattr(self.delegate, 'irc_channel_message'):
            self.delegate.irc_channel_message(client, nick, channel, message)

    def irc_channel_join(self, client: Client, nick: Nick, channel: Channel):
        if hasattr(self.delegate, 'irc_channel_join'):
            self.delegate.irc_channel_join(client, nick, channel)

    def irc_channel_quit(
        self, client: Client, nick: Nick, channel: Channel, message: Optional[str]
    ):
        if hasattr(self.delegate, 'irc_channel_quit'):
            self.delegate.irc_channel_quit(client, nick, channel, message)

    def irc_channel_part(
        self, client: Client, nick: Nick, channel, message: Optional[str]
    ):
        if hasattr(self.delegate, 'irc_channel_part'):
            self.delegate.irc_channel_part(client, nick, channel, message)

    def irc_channel_kick(
        self, client: Client, nick: Nick, channel: Channel, message: Optional[str]
    ):
        if hasattr(self.delegate, 'irc_channel_kick'):
            self.delegate.irc_channel_kick(client, nick, channel, message)

    def irc_channel_topic(self, client: Client, nick: Nick, channel: Channel):
        if hasattr(self.delegate, 'irc_channel_topic'):
            self.delegate.irc_channel_topic(client, nick, channel)
