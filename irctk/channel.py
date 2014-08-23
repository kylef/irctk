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

        self.nicks = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Chan %s>' % self.name

    def __in__(self, other):
        return other in self.nicks

    def send(self, message):
        self.client.send('PRIVMSG', self, message, force=True)

    def add_nick(self, nick):
        if self.client.nick == nick:
            self.is_attached = True
            self.client.send('MODE', self)

        if not self.has_nick(nick):
            self.nicks.append(nick)

    def remove_nick(self, nickname):
        nick = self.find_nick(nickname)
        if nick:
            self.nicks.remove(nick)

            if self.client.nick == nick:
                self.leave()

    def has_nick(self, nick):
        return bool(self.find_nick(nick))

    def find_nick(self, nickname):
        for nick in self.nicks:
            if nick == nickname:
                return nick

    def mode_change(self, modes):
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
            elif mode in self.client.isupport['prefix']:
                # Its a permission mode (like op, voice etc)

                nick = self.find_nick(args.pop(0))
                if nick:
                    if add:
                        nick.add_perm(mode)
                    else:
                        nick.remove_perm(mode)

            elif mode in self.client.isupport['chanmodes']:
                args_type = self.client.isupport['chanmodes'][mode]

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

    def join(self):
        self.client.send('JOIN', self)

    def part(self):
        self.client.send('PART', self)

