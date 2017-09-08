#!/usr/bin/env python

import asyncio
import irctk


class Bot:
    async def connect(self, hostname, port=6697, secure=True):
        client = irctk.Client()
        client.delegate = self
        await client.connect(hostname, port, secure)

    def irc_registered(self, client):
        channel = client.add_channel('#test')
        channel.join()

    def irc_private_message(self, client, nick, message):
        if message == 'ping':
            nick.send('pong')

    def irc_channel_message(self, client, nick, channel, message):
        if message == 'ping':
            channel.send('{}: pong'.format(nick))
        elif message == 'quit':
            client.quit()


if __name__ == '__main__':
    bot = Bot()

    loop = asyncio.get_event_loop()
    loop.create_task(bot.connect('irc.darkscience.net'))
    loop.run_forever()
