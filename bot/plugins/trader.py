import functools
import locale
import time

import requests

from peewee import IntegrityError
from disco.bot import Plugin, Config, CommandLevels
from disco.bot.command import CommandError
from disco.types.message import MessageEmbed

from bot.models.trader import Trader

CACHE_TTL = 120
INITIAL_BALANCE = 30000
GOOD_BALANCE = 0x77dd77
BAD_BALANCE = 0xff6961
IEX_URL = 'https://cloud.iexapis.com/stable'

locale.setlocale(locale.LC_ALL, '')


def require_trader(f):
    @functools.wraps(f)
    def wrapper(self, event, *args, **kwargs):
        trader = Trader.get_or_none(trader_id=event.author.id)
        if not trader:
            return event.msg.reply('Bro... you aren\'t ready to trade yet bro...')

        kwargs['trader'] = trader
        return f(self, event, *args, **kwargs)
    return wrapper


class TraderPluginConfig(Config):
    iex_api_key = ''


@Plugin.with_config(TraderPluginConfig)
class TraderPlugin(Plugin):
    def load(self, data):
        super().load(data)
        self._session = requests.Session()
        self._session.params['token'] = self.config.iex_api_key
        self._price_cache = {}

    def _get_price_for_entity(self, entity):
        if entity in self._price_cache:
            (ts, data) = self._price_cache[entity]
            if ts > time.time() - CACHE_TTL:
                return data
            del self._price_cache[entity]

        value = None
        if entity.startswith('$'):
            r = self._session.get(IEX_URL + '/stock/{}/price'.format(entity[1:].lower()))
            try:
                r.raise_for_status()
                value = r.json()
            except Exception:
                self.log.exception('Failed to fetch quote: ')
                raise CommandError('failed to fetch quote bro!')
        else:
            raise CommandError('only US stocks prefixed with `$` are supported right now bro...')

        self._price_cache[entity] = (time.time(), value)
        return value

    @Plugin.command('setup', aliases=['brome'], group='tr', level=CommandLevels.TRUSTED)
    def command_trader_setup(self, event):
        try:
            Trader.create(trader_id=event.author.id, balance=INITIAL_BALANCE)
        except IntegrityError:
            event.msg.reply('Bro... you are already setup to trade... cmon bro...')
            return

        event.msg.reply('Bro... welcome to the damn club bro...')

    @Plugin.command('balance', aliases=['bal', 'holdings'], group='tr', level=CommandLevels.TRUSTED)
    @require_trader
    def command_trader_balance(self, event, trader):
        embed = MessageEmbed()
        embed.title = 'Holdings'
        embed.set_footer(text=event.author.username, icon_url=event.author.avatar_url)
        embed.color = GOOD_BALANCE if trader.balance > 0 else BAD_BALANCE

        embed.description = ''
        total = trader.balance
        holdings = [('USD', '', trader.balance)]
        for name, amount in trader.holdings.items():
            entity_price = self._get_price_for_entity(name)
            holdings.append((name, amount, amount * entity_price))
            total += amount * entity_price

        holdings.append(('Total', '', total))

        for name, amount, value in holdings:
            embed.description += '**{}**: {} ({})\n'.format(
                name.upper(), amount, locale.currency(value, grouping=True)
            )

        event.msg.reply(embed=embed)

    @Plugin.command('quote', '<entity:str> [amount:int]', group='tr', level=CommandLevels.TRUSTED)
    def command_trader_quote(self, event, entity, amount=None):
        entity = entity.lower()
        price = self._get_price_for_entity(entity)

        if amount:
            event.msg.reply('{} Quote: ${} ({} @ ${})'.format(
                entity,
                amount * price,
                amount,
                price,
            ))
        else:
            event.msg.reply('{} Price: {}'.format(entity, price))

    @Plugin.command('buy', '<entity:str> <amount:int>', group='tr', level=CommandLevels.TRUSTED)
    @require_trader
    def command_trader_buy(self, event, entity, amount, trader):
        entity = entity.lower()
        price_per = self._get_price_for_entity(entity)
        price_total = price_per * amount
        if price_total > trader.balance:
            event.msg.reply('Bro... you are gonna need more money for that (${} required) bro...'.format(
                price_total,
            ))
            return

        current_amount = trader.holdings.get(entity, 0)

        up = Trader.update(
            balance=trader.balance - price_total,
            holdings=Trader.holdings[entity].set(current_amount + amount),
        ).where(
            (Trader.trader_id == trader.trader_id) &
            (Trader.balance == trader.balance)
        ).execute()
        if up != 1:
            self.log.error('Failed to update balance (buy) for {} / {} / {}'.format(
                entity,
                amount,
                trader.trader_id,
            ))
            raise CommandError('Bro... something went wrong bro :(')

        event.msg.reply('Bro... you now own {} (${}) of {} bro...'.format(
            amount,
            price_total,
            entity,
        ))

    @Plugin.command('sell', '<entity:str> <amount:int>', group='tr', level=CommandLevels.TRUSTED)
    @require_trader
    def command_trader_sell(self, event, entity, amount, trader):
        entity = entity.lower()
        if entity not in trader.holdings or trader.holdings[entity] <= 0:
            event.msg.reply('Bro... you don\'t hold any {} bro...'.format(entity))
            return

        current_amount = trader.holdings[entity]
        if current_amount < amount:
            event.msg.reply('Bro... you only have {}x {} to sell bro...'.format(entity, current_amount))
            return

        price = self._get_price_for_entity(entity)

        holdings_upd = None
        if current_amount - amount > 0:
            holdings_upd = Trader.holdings[entity].set(current_amount - amount)
        else:
            holdings_upd = Trader.holdings[entity].remove()

        up = Trader.update(
            balance=trader.balance + (price * amount),
            holdings=holdings_upd,
        ).where(
            (Trader.trader_id == trader.trader_id) &
            (Trader.balance == trader.balance)
        ).execute()
        if up != 1:
            self.log.error('Failed to update balance (sell) for {} / {} / {}'.format(
                entity,
                amount,
                trader.trader_id,
            ))
            raise CommandError('Bro... something went wrong bro :(')

        event.msg.reply('Bro... you sold {} of {} for ${} grats bro...'.format(
            amount,
            entity,
            price * amount,
        ))
