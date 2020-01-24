import re

from typing import Iterator


class ParseError(Exception):
    pass


class IRCUser:
    def __init__(
            self,
            nick,
            user: str = None,
            host: str = None,
            raw: str = None
    ):
        self.nick = nick
        self.user = user
        self.host = host
        self.raw = raw

    @classmethod
    def parse(cls, userstr: str) -> 'IRCUser':
        match = re.match(
            r'''
            : (?P<nick> [^!]+)
            (?:
              ! (?P<user>[^@]+)
            )?
            (?:
              @ (?P<host>.*)
            )?
            $
            ''',
            userstr,
            flags=re.VERBOSE,
        )
        if match is None:
            raise ParseError(userstr)

        user = cls(
            nick=match.group('nick'),
            user=match.group('user'),
            host=match.group('host'),
            raw=userstr,
        )
        return user

    @property
    def identity(self):
        return f"{self.user}@{self.host}"

    def __str__(self) -> str:
        def parts() -> Iterator[str]:
            yield f":{self.nick}"
            if self.user and self.host:
                yield f"!{self.identity}"

        return "".join(parts())
