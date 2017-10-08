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
    """
    Represents a channel
    """

    def __init__(self, name):
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
        """
        Channel name
        """

        return self.name

    def __repr__(self):
        return '<Channel %s>' % self.name

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
        self.members = []
