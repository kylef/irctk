from enum import Enum


class Command(Enum):
    # rfc1459 4.1 Connection Registration
    PASS = "PASS"
    NICK = "NICK"
    USER = "USER"
    OPER = "OPER"
    QUIT = "QUIT"

    # rfc1459 4.1 Channel Operations
    JOIN = "JOIN"
    PART = "PART"
    MODE = "MODE"
    TOPIC = "TOPIC"
    NAMES = "NAMES"
    LIST = "LIST"
    INVITE = "INVITE"
    KICK = "KICK"

    # rfc1459 4.3 Server queries and commands
    VERSION = "VERSION"

    # rfc1459 4.4 Sending messages
    PRIVMSG = "PRIVMSG"
    NOTICE = "NOTICE"

    # rfc1459 4.5 User-based queries
    WHO = "WHO"
    WHOIS = "WHOIS"
    WHOWAS = "WHOWAS"

    # rfc1459 4.6 Miscellaneous messages
    KILL = "KILL"
    PING = "PING"
    PONG = "PONG"
    ERROR = "ERROR"

    # rfc1459 5. Optionals
    AWAY = "AWAY"
    REHASH = "REHASH"
    ISON = "ISON"

    # IRCv3 Capabilities
    CAP = "CAP"

    # IRCv3: Message Tags
    TAGMSG = "TAGMSG"

    # IRCv3: Batches
    BATCH = "BATCH"

    # IRCv3: Chathistory
    CHATHISTORY = "CHATHISTORY"

    # IRCv3: Changehost
    CHGHOST = "CHGHOST"

    # IRCv3: Labeled Responses
    ACK = "ACK"

    # IRCv3: Monitor
    MONITOR = "MONITOR"

    # IRCv3: SASL
    AUTHENTICATE = "AUTHENTICATE"

    # IRCv3: Setname
    SETNAME = "SETNAME"

    # IRCv3: Standard Replies
    FAIL = "FAIL"
    WARN = "WARN"
    NOTE = "NOTE"

    # IRCv3 Read Marker (https://github.com/ircv3/ircv3-specifications/blob/3eba5f00deec75bb16bc2d7bdeef0decd6a5a978/extensions/read-marker.md)
    MARKREAD = "MARKREAD"

    def __str__(self) -> str:
        return self.value
