UPDATE stream_announcer_streams SET status = 'offline' WHERE twitch_name = ANY($1);
