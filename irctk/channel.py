from irctk.nick import Nick


class Membership(object):
    """
    Represents a nick membership inside a channnel.
    """

    def __init__(self, nick, modes=None):
        self.nick = nick
        self.modes = modes or []

    def has_perm(self, perm):
        return perm in self.modes

    def add_perm(self, perm):
        if not self.has_perm(perm):
            self.modes.append(perm)

    def remove_perm(self, perm):
        self.modes.remove(perm)


class Channel(object):
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self.modes = {}

        self.key = None

        self.is_attached = False

        self.creation_date = None

        self.topic = None
        self.topic_date = None
        self.topic_owner = None

        self.members = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Channel %s>' % self.name

    def __in__(self, other):
        return self.has_nick(other)

    def add_nick(self, nick):
        if self.client.nick == nick:
            self.is_attached = True
            self.client.send('MODE', self)

        if not self.has_nick(nick):
            self.members.append(Membership(nick))

    def add_membership(self, membership):
        if self.client.nick == membership.nick:
            self.is_attached = True
            self.client.send('MODE', self)

        if not self.has_nick(membership.nick):
            self.members.append(membership)

    def remove_nick(self, nickname):
        membership = self.find_membership(nickname)
        if membership:
            self.members.remove(membership)

            if self.client.nick == membership.nick:
                self.leave()

    def has_nick(self, nick):
        return bool(self.find_nick(nick))

    def find_membership(self, nickname):
        for membership in self.members:
            if membership.nick.nick == nickname:
                return membership

    def find_nick(self, nickname):
        membership = self.find_membership(nickname)
        if membership:
            return membership.nick

    def mode_change(self, modes, isupport):
        add = True
        args = []

        if ' ' in modes:
            modes, args = modes.split(' ', 1)
            args = args.split()

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

                elif args_type == None:
                    if add:
                        self.modes[mode] = True
                    elif mode in self.modes:
                        del self.modes[mode]

    def leave(self):
        self.is_attached = False
        self.nicks = []
