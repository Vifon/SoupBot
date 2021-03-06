from irc.message import IRCMessage
from irc.plugin import IRCPlugin


class PongPlugin(IRCPlugin):
    async def react(self, msg: IRCMessage) -> None:
        if msg.command == 'PING':
            self.client.send(IRCMessage('PONG', body=msg.body))
