import random
from disco.bot import Plugin, CommandLevels


class SpongePlugin(Plugin):
    def load(self, data):
        super(SpongePlugin, self).load(data)
        self._spongers = set()

    @Plugin.command('sponge', '<user:user>', level=CommandLevels.ADMIN)
    def command_sponge(self, event, user):
        if user.id in self._spongers:
            self._spongers.remove(user.id)
            event.msg.reply('no more sponge for them')
        else:
            self._spongers.add(user.id)
            event.msg.reply('spongey boiiii')

    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):
        if not event.content:
            return

        if event.author.id not in self._spongers:
            return

        if event.content.startswith('!'):
            return

        message = ''.join([
            char.upper() if idx % 2 == 0 else char.lower()
            for idx, char in enumerate(event.content)
        ])

        event.reply(message)
