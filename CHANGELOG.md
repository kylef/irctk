# irctk Changelog

## 0.3.0

### Enhancements

- `Client`s `send` method can now accept an instance of `Message`, which
  represents an IRC message.

- Support for negated ISUPPORTR parameters (server removing a feature)

- Added a numerics module.

- Added support for logging, the client now contains a logger which can be used
  to see raw IRC traffic in debug mode and other connection events in
  info/error levels.

- Ability to `await` send to get the response from a server in some cases. For
  example:

  ```python
  >>> message = await client.send('PING', 'hello')
  >>> message.command
  PONG
  ```

- Added support for [IRCv3 Message Tags](https://ircv3.net/specs/extensions/message-tags)

### Bug Fixes

- Numerous fixes around comparing nicks and channel names in the IRC compliance
  case-insensitive way.
