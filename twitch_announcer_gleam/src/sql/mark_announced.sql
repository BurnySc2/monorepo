UPDATE stream_announcer_streams SET announced_at = $1, status = 'online', last_seen_online = $1 WHERE twitch_name = ANY($2);
