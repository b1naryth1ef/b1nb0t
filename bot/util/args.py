import re

from disco.bot.command import CommandError

QUOTE_LINK_RE = re.compile(r'https://discordapp.com/channels/(\d+)/(\d+)/(\d+)')


def parse_message_arg(channel_id, message_raw):
    message_id = None

    if message_raw.isdigit():
        message_id = int(message_raw)
    else:
        res = QUOTE_LINK_RE.findall(message_raw)
        if res:
            channel_id = int(res[0][1])
            message_id = int(res[0][2])

    if not message_id:
        raise CommandError("invalid message id or link provided")

    return channel_id, message_id
