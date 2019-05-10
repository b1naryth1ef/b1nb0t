from bot.models import BaseModel
from peewee import IntegerField, CharField


@BaseModel.register
class Tag(BaseModel):
    class Meta:
        table_name = 'tags'

    author_id = IntegerField()
    name = CharField()
    value = CharField()
