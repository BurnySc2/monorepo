"""Base file for models"""
from pony import orm  # pyre-fixme[21]

db = orm.Database()
