irctk
=====

An IRC client toolkit in Python.

## Installation

```bash
$ pip install irctk
```

## Usage

```python
import zokket
import irctk

class PingBot(object):
    def __init__(self):
        client = irctk.Client()
        client.delegate = self
        client.connect('chat.freenode.net', 6697, secure=True)

    def irc_registered(self, client):
        channel = client.add_channel('#test')
        channel.join()

    def irc_private_message(self, client, nick, message):
        if message == 'ping':
            nick.send('pong')

    def irc_channel_message(self, client, nick, channel, message):
        if message == 'ping':
            channel.send('{}: pong'.format(nick))

if __name__ == '__main__':
    bot = PingBot()
    zokket.DefaultRunloop.run()
```

