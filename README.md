irc-toolkit
===========

An IRC client toolkit in Python.

## Installation

```bash
$ pip install irc-toolkit
```

## Usage

There are a few parts of irc-toolkit, depending on your goals.
[`irctk.Message`](https://irctk.readthedocs.io/en/latest/message.html)
offers IRC message parsing,
[`irctk.Client`](https://irctk.readthedocs.io/en/latest/client.html) offers an
IRC client which handles connection/channel/nick tracking giving you a callback
based interface for IRC messages, for example:

```python
#!/usr/bin/env python

import asyncio
import logging

import irctk


class Bot:
    async def connect(self, hostname, port=6697, secure=True):
        client = irctk.Client()
        client.delegate = self
        await client.connect(hostname, port, secure)

    def irc_registered(self, client):
        client.send('MODE', client.nick, '+B')
        client.send('JOIN', '#test')

    def irc_private_message(self, client, nick, message):
        if message == 'ping':
            client.send('PRIVMSG', nick, 'pong')

    def irc_channel_message(self, client, nick, channel, message):
        if message == 'ping':
            client.send('PRIVMSG', channel, f'{nick}: pong')
        elif message == 'quit':
            client.quit()


if __name__ == '__main__':
    # Enable debug logging
    logging.basicConfig(level='DEBUG')

    bot = Bot()
    asyncio.run(bot.connect('irc.darkscience.net'))
```
