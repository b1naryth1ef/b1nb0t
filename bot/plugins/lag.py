import time
import random

from disco.bot import Plugin, CommandLevels


class LagPlugin(Plugin):
    @Plugin.command('embed', group='lag', level=CommandLevels.MOD)
    def command_lag_embed(self, event):
        uid = random.randint(1, 100000000)

        msg = event.msg.reply(f'https://files.hydr0.com/yeet.png?{uid}')

        start = time.time()
        self.wait_for_event('MessageUpdate', message__id=msg.id)
        msg.edit(f'Took {time.time() - start}s to embed')
