from piccolo.table import Table
from piccolo.columns import Integer, Text, Timestamp

class Reminder(Table, tablename="reminder"):
    reminder_utc = Timestamp(required=True)
    user_id = Integer(required=True)
    user_name = Text(required=True)
    guild_id = Integer(required=True)
    channel_id = Integer(required=True)
    message = Text(required=True)
    message_id = Integer(required=True)
