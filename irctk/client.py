from typing import List, Dict, Optional, NamedTuple
import datetime
import string
import asyncio
import logging

from irctk.isupport import ISupport
from irctk.nick import Nick
from irctk.channel import Channel, Membership
from irctk.message import Message


def find_tag(name: str, message: Message):
    for tag in message.tags:
        if tag.name == name:
            return tag.value


class Request(NamedTuple):
    message: Message
    future: asyncio.Future


class IRCIgnoreLine(Exception):
    pass


class Client:
    """
    >>> client = Client(nickname='example')
    """

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
        self.nick = self.nick_class()

        self.channels: List[Channel] = []
        self.isupport = ISupport()

        self.cap_accepted: List[str] = []
        self.cap_pending: List[str] = []

        self.modules: List = []

        self.requests: List[Request] = []

        self.batches: Dict[str, List[Message]] = {}

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

        await self.connected()

    async def read(self) -> Optional[Message]:
        raw_message = await self.reader.readline()
        if not raw_message:
            return None

        line = raw_message.decode('utf-8').strip()
        self.logger.debug('S: {}'.format(line))
        return Message.parse(line)

    async def connected(self):
        self.is_connected = True
        self.authenticate()
        await self.writer.drain()

        while self.is_connected:
            message = await self.read()

            if not message:
                self.is_registered = False
                self.is_connected = False
                self.writer.close()
                self.irc_disconnected(None)
                self.logger.info('Disconnected')
                return

            self.process_message(message)
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

    def is_channel(self, channel: str) -> bool:
        return self.isupport.is_channel(channel)

    def find_channel(self, name: Optional[str]) -> Optional[Channel]:
        if not name:
            return None

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
        """
        Send an IRC message

        >>> client.send('JOIN', '#example')
        """

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

        if find_tag('label', message):
            loop = asyncio.get_event_loop()
            future = loop.create_future()

            self.requests.append(Request(message=message, future=future))
            return future

        if message.command == 'NICK':
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            self.requests.append(Request(message=message, future=future))
            return future

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

    def process_line(self, line: str):
        return self.process_message(Message.parse(line))

    def process_message(self, message: Message):
        try:
            self.irc_raw(str(message))
        except IRCIgnoreLine:
            return

        self.irc_message(message)

        if message.command == 'BATCH' and len(message.parameters) > 0:
            if message.parameters[0].startswith('+'):
                reference_tag = message.parameters[0][1:]
                self.batches[reference_tag] = [message]
            elif message.parameters[0].startswith('-'):
                reference_tag = message.parameters[0][1:]

                if reference_tag in self.batches:
                    batch = self.batches[reference_tag]
                    batch.append(message)
                    del self.batches[reference_tag]

                    label = find_tag('label', batch[0])
                    for request in self.requests:
                        if find_tag('label', request.message) == label:
                            self.requests.remove(request)
                            request.future.set_result(batch)
                            break

        reference_tag = find_tag('batch', message)
        if reference_tag and reference_tag in self.batches:
            self.batches[reference_tag].append(message)

        command = message.command.lower()
        if hasattr(self, 'process_{}'.format(command)):
            func = getattr(self, 'process_{}'.format(command))
            func(message)

        label = find_tag('label', message)
        if label and message.command != 'BATCH':
            for request in self.requests:
                if find_tag('label', request.message) == label:
                    self.requests.remove(request)
                    request.future.set_result(message)

    def process_001(self, message: Message):
        self.is_registered = True
        self.nick.nick = message.parameters[0]

        for request in self.requests:
            if (
                request.message.command == 'NICK'
                and find_tag('label', request.message) is None
                and len(request.message.parameters) > 0
                and self.irc_equal(self.nick.nick, request.message.parameters[0])
            ):
                self.requests.remove(request)
                request.future.set_result(message)

        self.send('WHO', self.nick)
        self.irc_registered()

    def process_005(self, message: Message):
        self.isupport.parse(message.parameters[1])

    def process_324(self, message: Message):  # MODE
        channel = self.find_channel(message.get(1))
        if channel:
            channel.modes = {}
            channel.mode_change(' '.join(message.parameters[2:]), self.isupport)

    def process_329(self, message: Message):
        channel = self.find_channel(message.get(1))
        timestamp = message.get(2)
        if channel and timestamp:
            channel.creation_date = datetime.datetime.fromtimestamp(int(timestamp))

    def process_332(self, message: Message):
        channel = self.find_channel(message.get(1))
        if channel:
            channel.topic = message.get(2)

    def process_333(self, message: Message):
        channel = self.find_channel(message.get(1))
        if channel:
            channel.topic_owner = message.get(2)

            topic_date = message.get(3)
            if topic_date:
                channel.topic_date = datetime.datetime.fromtimestamp(int(topic_date))

    # RPL_WHOREPLY
    def process_352(self, message: Message):
        nick = message.get(5)

        if nick and self.irc_equal(self.nick.nick, nick):
            self.nick.ident = message.get(2)
            self.nick.host = message.get(3)

    def process_432(self, message: Message):
        # Erroneous Nickname: Illegal characters
        self.process_433(message)

    def process_436(self, message: Message):
        # Nickname collision
        self.process_433(message)

    def process_433(self, message: Message):
        # Nickname is already in use
        if not self.is_registered:
            self.send('NICK', self.get_alt_nickname())

        if len(message.parameters) > 1:
            nick = message.parameters[1]

            for request in self.requests:
                if (
                    request.message.command == 'NICK'
                    and find_tag('label', request.message) is None
                    and len(request.message.parameters) > 0
                    and self.irc_equal(nick, request.message.parameters[0])
                ):
                    self.requests.remove(request)
                    request.future.set_exception(Exception(message))
                    break

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

    def process_353(self, message: Message):
        channel = self.find_channel(message.get(2))
        users = message.get(3)
        if channel and users:
            for user in users.split():
                membership = self.names_353_to_membership(user)
                self.channel_add_membership(channel, membership)

    def process_431(self, message: Message):
        for request in self.requests:
            if (
                request.message.command == 'NICK'
                and find_tag('label', request.message) is None
                and len(request.message.parameters) == 0
            ):
                self.requests.remove(request)
                request.future.set_exception(Exception(message))
                break

    def process_ping(self, message: Message):
        self.send('PONG', ' '.join(message.parameters))

    def process_cap(self, message: Message):
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

    def process_join(self, message: Message):
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

    def process_part(self, message: Message):
        channel = self.find_channel(message.get(0))
        if channel:
            nick = self.nick_class.parse(message.prefix)
            reason = message.get(1)

            self.channel_remove_nick(channel, nick)
            self.irc_channel_part(nick, channel, reason)

    def process_kick(self, message: Message):
        channel = self.find_channel(message.get(0))
        kicked_nickname = message.get(1)
        if channel and kicked_nickname:
            kicked_nick = self.nick_class(nick=kicked_nickname)
            reason = message.get(2)

            nick = self.nick_class.parse(message.prefix)
            self.channel_remove_nick(channel, kicked_nick)
            self.irc_channel_kick(nick, channel, reason)

    def process_topic(self, message: Message):
        channel = self.find_channel(message.get(0))
        if channel:
            nick = self.nick_class.parse(message.prefix)
            channel.topic = message.get(1)
            channel.topic_owner = nick
            channel.topic_date = datetime.datetime.now()

            self.irc_channel_topic(nick, channel)

    def process_nick(self, message: Message):
        nick = self.nick_class.parse(message.prefix)
        new_nick = message.get(0)
        if not new_nick:
            return

        if self.irc_equal(self.nick.nick, nick.nick):
            self.nick.nick = new_nick

        for channel in self.channels:
            for membership in channel.members:
                if self.irc_equal(membership.nick.nick, nick.nick):
                    membership.nick.nick = new_nick

        for request in self.requests:
            if (
                request.message.command == 'NICK'
                and find_tag('label', request.message) is None
                and len(request.message.parameters) > 0
                and self.irc_equal(new_nick, request.message.parameters[0])
            ):
                self.requests.remove(request)
                request.future.set_result(message)
                break

    def process_privmsg(self, message: Message):
        sender = self.nick_class.parse(message.prefix)
        target = message.get(0)
        text = message.get(1)
        if not target or not text:
            return

        if self.irc_equal(target, self.nick.nick):
            self.irc_private_message(sender, text)
        else:
            channel = self.find_channel(target)
            if channel:
                self.irc_channel_message(sender, channel, text)

    def process_mode(self, message: Message):
        subject = message.get(0)

        if subject and self.is_channel(subject):
            channel = self.find_channel(subject)

            if channel:
                mode_line = ' '.join(message.parameters[1:])
                channel.mode_change(mode_line, self.isupport)

    def process_quit(self, message: Message):
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
