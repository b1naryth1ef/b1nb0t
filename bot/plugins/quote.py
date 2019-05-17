from disco.bot import Plugin, CommandLevels
from disco.types.message import MessageEmbed
from bot.util.args import parse_message_arg


class QuotePlugin(Plugin):
    @Plugin.command('quote', '<message_raw:str>', level=CommandLevels.TRUSTED)
    def command_quote(self, event, message_raw):
        channel_id, message_id = parse_message_arg(event.channel_id, message_raw)
        message = self.state.channels.get(channel_id).get_message(message_id)

        embed = MessageEmbed()
        embed.set_author(
            name=message.author.username,
            icon_url=message.author.avatar_url,
        )
        url = 'https://discordapp.com/channels/{}/{}/{}'.format(
            message.channel.guild.id,
            message.channel.id,
            message.id,
        )
        embed.description = message.content + '\n\n[view]({})'.format(
            url
        )
        embed.set_footer(text="#{} in {}".format(
            message.channel.name,
            message.channel.guild.name,
        ))
        embed.timestamp = message.timestamp.isoformat()
        event.msg.reply(embed=embed)
