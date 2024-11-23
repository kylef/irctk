from irctk.command import Command


def test_command():
    command = Command.PRIVMSG
    assert command.value == 'PRIVMSG'
    assert str(command) == 'PRIVMSG'


def test_all_commands():
    for command in list(Command):
        # name must equal the value
        assert command.name == command.value

        # value must be uppercased
        assert command.value.isupper()
