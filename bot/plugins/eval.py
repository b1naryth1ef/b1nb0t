import pprint


from disco.bot import Plugin, CommandLevels
from bot.util.args import parse_message_arg

PY_CODE_BLOCK = '```py\n{}\n```'


class EvalPlugin(Plugin):
    @Plugin.command('eval', level=CommandLevels.ADMIN)
    def command_eval(self, event):
        ctx = {
            'bot': self.bot,
            'client': self.bot.client,
            'state': self.bot.client.state,
            'event': event,
            'msg': event.msg,
            'guild': event.msg.guild,
            'channel': event.msg.channel,
            'author': event.msg.author
        }

        code = event.codeblock
        if '\n' not in code:
            try:
                result = eval(code, ctx)
            except Exception as e:
                event.msg.reply(PY_CODE_BLOCK.format(type(e).__name__ + ': ' + str(e)))
                return

            event.msg.reply(PY_CODE_BLOCK.format(result))
        else:
            lines = list(filter(bool, code.split('\n')))
            if lines[-1] and 'return' not in lines[-1]:
                lines[-1] = 'return ' + lines[-1]
            lines = '\n'.join('    ' + i for i in lines)
            wrapped_code = 'def f():\n{}\nx = f()'.format(lines)
            local = {}

            try:
                exec(compile(wrapped_code, '<eval>', 'exec'), ctx, local)
            except Exception as e:
                event.msg.reply(PY_CODE_BLOCK.format(type(e).__name__ + ': ' + str(e)))
                return

            event.msg.reply(PY_CODE_BLOCK.format(pprint.pformat(local['x'])))

    @Plugin.command('source', '<message_raw:str>', level=CommandLevels.ADMIN)
    def command_source(self, event, message_raw):
        channel_id, message_id = parse_message_arg(event.channel.id, message_raw)
        message = self.state.channels.get(channel_id).get_message(message_id)

        event.msg.reply('```{}```'.format(
            pprint.pformat(message.to_dict())
        ))
