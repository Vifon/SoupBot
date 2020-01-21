from irc.plugin import IRCPlugin
import itertools
import re


class UserScore(IRCPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        c = self.db.cursor()
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS score
            (
                nick STRING,
                channel STRING,
                score INTEGER,
                UNIQUE(nick, channel)
            )
            '''
        )

    def match(self, msg):
        if msg.command == 'PRIVMSG':
            channel = msg.args[0]
            if not channel.startswith("#"):
                return
            names = self.client.shared_data.NameTrack[channel]
            scorables = itertools.chain(self.config['scorables'], names)
            name_re = "|".join(map(re.escape, scorables))
            operators = ["++", "--"]
            operator_re = "|".join(map(re.escape, operators))
            separator_re = r'[^\w+-]'
            match = re.search(
                fr'''
                (?:{separator_re}|^)
                (?P<op1>{operator_re})
                (?P<nick1>{name_re})
                (?:{separator_re}|$)
                |
                (?:{separator_re}|^)
                (?P<nick2>{name_re})
                (?P<op2>{operator_re})
                (?:{separator_re}|$)
                ''',
                msg.body,
                flags=re.VERBOSE,
            )
            if match:
                nick = match.group('nick1') or match.group('nick2')
                op = match.group('op1') or match.group('op2')
                return msg.sender.nick, nick, channel, op

    def respond(self, data):
        sender, nick, channel, operator = data

        if sender == nick:
            self.client.send('PRIVMSG', channel, body=f"{sender}: No self-scoring!")
            return

        value_map = {
            '++': +1,
            '--': -1,
        }
        change = value_map[operator]
        self.change_score(nick, channel, change)
        score = self.score(nick, channel)
        self.client.send('PRIVMSG', channel, body=f"{nick}'s score is now {score}.")

    def score(self, nick, channel):
        c = self.db.cursor()
        c.execute(
            '''
            SELECT score FROM score
            WHERE nick=? AND channel=?
            ''',
            (nick, channel)
        )
        value = c.fetchone()
        if value is None:
            return 0
        else:
            return value[0]

    def change_score(self, nick, channel, change):
        c = self.db.cursor()
        c.execute(
            '''
            INSERT INTO score
            (nick, channel, score)
            VALUES (?, ?, ?)
            ON CONFLICT(nick, channel) DO
            UPDATE SET score = score + ?
            ''',
            (nick, channel, change, change)
        )
        self.db.commit()