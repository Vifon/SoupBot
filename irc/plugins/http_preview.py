from irc.plugin import IRCPlugin

from bs4 import BeautifulSoup
from urlextract import URLExtract
import aiohttp
import asyncio


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


class HTTPPreview(IRCPlugin):
    extractor = URLExtract()

    async def react(self, msg):
        if msg.command == 'PRIVMSG':
            channel = msg.args[0]
            nick = msg.sender.nick
            for url in self.extractor.gen_urls(msg.body):
                try:
                    async with aiohttp.ClientSession() as session:
                        try:
                            html = await asyncio.wait_for(
                                fetch(session, url),
                                timeout=self.config.get('timeout', 10),
                            )
                        except asyncio.TimeoutError:
                            await self.client.send(
                                'PRIVMSG', channel,
                                body=f"{nick}: Request timed out.",
                            )
                            raise
                        else:
                            soup = BeautifulSoup(html, 'html.parser')
                            title = soup.title.get_text()
                            await self.client.send(
                                'PRIVMSG', channel,
                                body=f"{nick}: {title}",
                            )
                except Exception:
                    self.logger.exception("Error during processing %s", url)