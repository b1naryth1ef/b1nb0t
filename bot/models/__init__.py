import os
from peewee import Model, Proxy
from playhouse.sqlite_ext import SqliteExtDatabase, JSONField


__all__ = [
    'JSONField',
    'BaseModel',
    'database',
    'REGISTERED_MODELS',
    'init_db',
]


REGISTERED_MODELS = []

# Create a database proxy we can setup post-init
database = Proxy()


class BaseModel(Model):
    class Meta:
        database = database

    @staticmethod
    def register(cls):
        REGISTERED_MODELS.append(cls)
        return cls

    @classmethod
    def with_id(cls, oid, *fields):
        try:
            return cls.select(*fields).get(oid)
        except cls.DoesNotExist:
            return None


def init_db():
    for file_name in os.listdir(os.path.dirname(os.path.abspath(__file__))):
        if file_name.startswith('_') or not file_name.endswith('.py'):
            continue

        __import__('bot.models.{}'.format(os.path.splitext(os.path.basename(file_name))[0]))

    database.initialize(SqliteExtDatabase('b1nb0t.db', pragmas=[
        ('foreign_keys', 1)
    ], check_same_thread=False))

    for model in REGISTERED_MODELS:
        model.create_table(True)


init_db()
