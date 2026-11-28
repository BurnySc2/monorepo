UPDATE stream_announcer_streams SET status = 'online', last_seen_online = $1 WHERE twitch_name = ANY($2);
