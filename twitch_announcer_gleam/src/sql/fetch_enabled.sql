SELECT twitch_name, discord_webhook, announce_message, status, last_seen_online, announced_at FROM stream_announcer_streams WHERE enabled IS TRUE ORDER BY id;
