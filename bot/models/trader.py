from bot.models import BaseModel, JSONField
from peewee import FloatField, IntegerField


@BaseModel.register
class Trader(BaseModel):
    class Meta:
        table_name = 'traders'

    trader_id = IntegerField(unique=True)
    balance = FloatField(null=False)
    holdings = JSONField(default={})
