#!/usr/bin/env python

import zokket
import irctk


class Bot(object):
    def __init__(self, hostname, port=6697, secure=True):
        client = irctk.Client()
        client.delegate = self
        client.connect(hostname, port, secure)

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
    bot = Bot('irc.darkscience.net')
    zokket.DefaultRunloop.run()

