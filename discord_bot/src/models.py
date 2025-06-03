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

class DiscordMessage(Table, tablename="discord_message"):
    guild_id = Integer(required=True)
    channel_id = Integer(required=True)
    autho_id= Integer(required=True)
    message_id = Integer(required=True)
    who = Text(required=True)
    when= Timestamp(required=True)
    what= Text(required=True)

class DiscordQuote(Table, tablename="discord_quote"):
    guild_id = Integer(required=True)
    channel_id = Integer(required=True)
    autho_id= Integer(required=True)
    message_id = Integer(required=True)
    who = Text(required=True)
    when= Timestamp(required=True)
    what= Text(required=True)
    emoji_name= Text(required=True)
