from disco.bot import Plugin, CommandLevels
from disco.types.message import MessageEmbed
from disco.util.sanitize import S
from disco.bot.command import USER_MENTION_RE
from bot.models.tags import Tag


class TagsPlugin(Plugin):
    @Plugin.command('create', group='tags', aliases=['add'], level=CommandLevels.TRUSTED, parser=True)
    @Plugin.parser.add_argument('name', type=str)
    @Plugin.parser.add_argument('value', type=str, nargs='+')
    def command_tags_create(self, event, args):
        _, created = Tag.get_or_create(
            name=S(args.name.lower()),
            defaults={
                'value': S(' '.join(args.value)),
                'author_id': event.author.id,
            }
        )
        if not created:
            event.msg.reply('a tag by that name already exists')
            return

        event.msg.reply('ok created that tag for you')

    @Plugin.command('update', group='tags', aliases=['upd'], level=CommandLevels.TRUSTED, parser=True)
    @Plugin.parser.add_argument('name', type=str)
    @Plugin.parser.add_argument('value', type=str, nargs='+')
    def command_tags_update(self, event, args):
        updated = Tag.update(value=S(' '.join(args.value))).where(
            (Tag.name == S(args.name.lower()))
        ).execute()
        if not updated:
            event.msg.reply('no tag by that name exists')
        else:
            event.msg.reply('ok updated that tag for you')

    @Plugin.command('delete', group='tags', aliases=['del', 'rm'], level=CommandLevels.TRUSTED, parser=True)
    @Plugin.parser.add_argument('name', type=str)
    def command_tags_delete(self, event, args):
        deleted = Tag.delete().where(
            (Tag.name == S(args.name.lower()))
        ).execute()
        if deleted:
            event.msg.reply('ok deleted that tag for you')
        else:
            event.msg.reply('no tag exists by that name')

    @Plugin.command('search', group='tags', level=CommandLevels.TRUSTED, parser=True)
    @Plugin.parser.add_argument('--name', type=str)
    @Plugin.parser.add_argument('--value', type=str)
    @Plugin.parser.add_argument('--author', type=str)
    def command_tags_search(self, event, args):
        query = Tag.select()

        if args.name:
            query = query.where(Tag.name ** '%{}%'.format(S(args.name.lower())))

        if args.value:
            query = query.where(Tag.value ** '%{}%'.format(S(args.value.lower())))

        if args.author:
            if args.author.isdigit():
                query = query.where(Tag.author_id == int(args.author))
            else:
                matches = USER_MENTION_RE.findall(args.author)
                if not matches:
                    return event.msg.reply('invalid author argument')

                query = query.where(Tag.author_id == int(matches[0]))

        query = query.limit(50)

        event.msg.reply('Results: {}'.format(', '.join(i.name for i in query)))

    @Plugin.command('tag', level=CommandLevels.TRUSTED, parser=True)
    @Plugin.parser.add_argument('name', type=str)
    @Plugin.parser.add_argument('--full', '-f', action='store_true', default=False)
    def command_tag(self, event, args):
        tag = Tag.get_or_none(name=S(args.name.lower()))
        if not tag:
            event.msg.reply('no tag by that name buddo')
            return

        if args.full:
            embed = MessageEmbed()
            embed.description = tag.value
            embed.title = tag.name

            user = self.state.users.get(tag.author_id)
            if user:
                embed.set_footer(text=user.username, icon_url=user.avatar_url)
            else:
                embed.set_footer(text='unknown user')

            event.msg.reply(embed=embed)
        else:
            event.msg.reply(tag.value)
