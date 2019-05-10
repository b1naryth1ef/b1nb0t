from disco.bot import Plugin, CommandLevels


IDIOT_IDS = [
    184496454067421185,
    106195890703724544,
]


class TylerPlugin(Plugin):
    def load(self, data):
        super(TylerPlugin, self).load(data)
        self._enabled = True

    @Plugin.command('enable', group='tyler', level=CommandLevels.ADMIN)
    @Plugin.command('disable', group='tyler', level=CommandLevels.ADMIN)
    def command_tyler_enable(self, event):
        want_value = True if event.name == 'enable' else False

        if want_value is self._enabled:
            event.msg.reply('Tyler protection is already {}d'.format(event.name))
        else:
            self._enabled = want_value
            event.msg.reply('Ok, I\'ve {}d Tyler protection'.format(event.name))

    @Plugin.listen('MessageCreate')
    def on_message_create(self, event):
        if not self._enabled:
            return

        if event.author.id not in IDIOT_IDS:
            return

        if 'tenor.com' in event.content:
            event.delete()
            event.reply('{} No.'.format(event.author.mention))
