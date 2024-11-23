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
