from mcipc.rcon import Client

from disco.bot import Plugin, Config
from disco.types.message import MessageEmbed

JOIN_COLOR = 0x77dd77
LEAVE_COLOR = 0xff6961


class MinecraftPluginConfig(Config):
    ip = ''
    port = 0
    password = ''
    channel_id = ''


@Plugin.with_config(MinecraftPluginConfig)
class MinecraftPlugin(Plugin):
    def load(self, data):
        super().load(data)
        self._online = None

    @Plugin.schedule(20, init=True)
    def on_schedule(self):
        self.state.ready.wait()

        players = self.get_players()
        if not players:
            return

        channel = self.state.channels.get(self.config.channel_id)
        if not channel:
            print('failed to find channel')
            return

        names = set(players.names)
        if self._online is not None and names != self._online:
            connected = names - self._online

            for conn in connected:
                embed = MessageEmbed()
                embed.color = JOIN_COLOR
                embed.title = '{} joined the server'.format(conn)
                channel.send_message(embed=embed)

            disconnected = self._online - names
            for conn in disconnected:
                embed = MessageEmbed()
                embed.color = LEAVE_COLOR
                embed.title = '{} left the server'.format(conn)
                channel.send_message(embed=embed)

        if self._online is None:
            print('Initial Online: {}'.format(names))

        self._online = names

    def get_players(self):
        try:
            with Client(self.config.ip, self.config.port) as client:
                client.login(self.config.password)
                return client.players
        except Exception:
            self.log.exception('Failed to query minecraft RCON: ')
