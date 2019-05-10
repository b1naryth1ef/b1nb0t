import os
import json
import sqlite3
import requests
from datetime import datetime

from disco.bot import Plugin, CommandLevels
from disco.bot.command import CommandError
from disco.types.channel import MessageIterator, ChannelType


def _default_json(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError('Type %s is not serializable' % type(obj))


def _message_serializer(log, chunk):
    for message in chunk:
        try:
            data = message.to_dict()
            data['mentions'] = list(data['mentions'].keys())
            data['attachments'] = {k: v.to_dict() for k, v in data['attachments'].items()}
            yield (message.id, json.dumps(data, default=_default_json))
        except Exception:
            log.exception(f'Failed to serialize message {message.id} / {message.channel_id}')
            raise


def _message_attachment_serializer(log, chunk):
    session = requests.Session()

    for message in chunk:
        for attachment in message.attachments.values():
            try:
                r = session.get(attachment.url)
                r.raise_for_status()
                yield (attachment.id, r.content)
            except Exception:
                log.exception(f'Failed to download attachment {attachment.id} / {message.id} / {message.channel_id}')


def _channel_ident_to_channel_id(guild, channel_ident):
    if channel_ident.isdigit():
        if int(channel_ident) not in guild.channels:
            return None
        return int(channel_ident)

    return guild.channels.select_one(name=channel_ident).id


class BackupPlugin(Plugin):
    @Plugin.command('backup', aliases=['bkup'], level=CommandLevels.MOD, parser=True, oob=True)
    @Plugin.parser.add_argument('name', type=str)
    @Plugin.parser.add_argument('-e', '--exclude-channel', type=str, nargs='+')
    @Plugin.parser.add_argument('-i', '--include-channel', type=str, nargs='+')
    @Plugin.parser.add_argument('-d', '--dl-attachments', action='store_true', default=False)
    def command_backup(self, event, args):
        if args.include_channel:
            channel_ids = set()

            for channel_ident in args.include_channel:
                channel_id = _channel_ident_to_channel_id(event.guild, channel_ident)
                if not channel_id:
                    raise CommandError(f'invalid channel to include `{channel_ident}`')
                channel_ids.add(channel_id)
        else:
            channel_ids = set(i.id for i in event.guild.channels.values() if i.type == ChannelType.GUILD_TEXT)

        if args.exclude_channel:
            for channel_ident in args.exclude_channel:
                channel_id = _channel_ident_to_channel_id(event.guild, channel_ident)
                if not channel_id:
                    raise CommandError(f'invalid channel to exclude `{channel_ident}`')
                channel_ids.remove(channel_id)

        backup = self._open_backup(args.name)

        messages_count = 0
        message = event.msg.reply('Preparing to backup...')
        for idx, channel_id in enumerate(channel_ids):
            channel = event.guild.channels[channel_id]
            message.edit(
                f'Backing up channel {channel.mention} ({idx+1}/{len(channel_ids)} | {messages_count} total messages)'
            )
            messages_count += self._backup_channel(backup, channel, args.dl_attachments)

        message.edit(f'Backup complete, a total of {messages_count} messages where preserved')
        backup.close()

    def _open_backup(self, name):
        if os.path.exists(f'{name}.db'):
            raise CommandError(f'a backup by the name {name} already exists')

        conn = sqlite3.connect(f'{name}.db')
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER, data TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS attachments (id INTEGER, data BLOB)')
        conn.commit()
        return conn

    def _backup_channel(self, conn, channel, download_attachments):
        self.log.info(f'Starting downward messages iterator for channel {channel.id} {channel.name}')

        cursor = conn.cursor()

        count = 0
        for chunk in channel.messages_iter(bulk=True, after=1, direction=MessageIterator.Direction.DOWN):
            count += len(chunk)
            cursor.executemany(
                'INSERT INTO messages (id, data) VALUES (?, ?)',
                _message_serializer(self.log, chunk),
            )
            conn.commit()

            if download_attachments:
                cursor.executemany(
                    'INSERT INTO attachments (id, data) VALUES (?, ?)',
                    _message_attachment_serializer(self.log, chunk),
                )
                conn.commit()

        return count
