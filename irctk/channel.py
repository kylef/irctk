from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from irctk.isupport import ISupport
from irctk.nick import Nick


class Membership(object):
    """
    Represents a nick membership inside a channnel.
    """

    def __init__(self, nick: Nick, modes: Optional[List[str]] = None):
        self.nick = nick
        self.modes = modes or []

    def has_mode(self, perm: str) -> bool:
        """
        Checks if the membership contains a user mode

        >>> membership.has_mode('o')
        """

        return perm in self.modes

    def add_perm(self, perm: str) -> None:
        if not self.has_mode(perm):
            self.modes.append(perm)

    def remove_perm(self, perm: str) -> None:
        self.modes.remove(perm)


class Channel(object):
    """
    Represents a channel
    """

    def __init__(self, name: str):
        self.name = name
        self.modes: Dict[str, Any] = {}

        self.key: Optional[str] = None

        self.is_attached = False

        self.creation_date: Optional[datetime] = None

        self.topic: Optional[str] = None
        self.topic_date: Optional[datetime] = None
        self.topic_owner: Optional[Union[str, Nick]] = None

        self.members: List[Membership] = []

    def __str__(self) -> str:
        """
        Channel name
        """

        return self.name

    def __repr__(self) -> str:
        return '<Channel %s>' % self.name

    def find_member(self, nickname: str) -> Optional[Membership]:
        for member in self.members:
            if member.nick.nick == nickname:
                return member

        return None

    def mode_change(self, modes: str, isupport: ISupport) -> None:
        add = True
        args: List[str] = []

        if ' ' in modes:
            modes, args_string = modes.split(' ', 1)
            args = args_string.split()

        for mode in modes:
            if mode == '+':
                add = True
            elif mode == '-':
                add = False
            elif mode in isupport['prefix']:
                # Its a permission mode (like op, voice etc)

                membership = self.find_member(args.pop(0))
                if membership:
                    if add:
                        membership.add_perm(mode)
                    else:
                        membership.remove_perm(mode)

            elif mode in isupport['chanmodes']:
                args_type = isupport['chanmodes'][mode]

                if args_type == list:
                    if mode not in self.modes:
                        self.modes[mode] = []

                    if add:
                        self.modes[mode].append(args.pop(0))
                    else:
                        self.modes[mode].remove(args.pop(0))

                elif args_type == 'arg':
                    arg = args.pop(0)

                    if add:
                        self.modes[mode] = arg
                    elif mode in self.modes and self.modes[mode] == arg:
                        del self.modes[mode]

                elif args_type == 'arg_set':
                    if add:
                        self.modes[mode] = args.pop(0)
                    else:
                        if mode in self.modes:
                            del self.modes[mode]

                elif args_type is None:
                    if add:
                        self.modes[mode] = True
                    elif mode in self.modes:
                        del self.modes[mode]

    def leave(self) -> None:
        self.is_attached = False
        self.members = []
