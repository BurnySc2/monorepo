# Compile with nimble

```sh
# Compile in fastest mode
nimble c -d:ssl -d:release -o:main src/main.nim
# nimble c -d:ssl -d:danger -o:main src/main.nim
# Run
./main
```

# Build slim image

https://github.com/slimtoolkit/slim

```sh
docker build -t burnysc2/twitch_stream_announcer:local .
slim build --target burnysc2/twitch_stream_announcer:local --tag burnysc2/twitch_stream_announcer:latest--http-probe=false --env STAGE=BUILD --exec "/root/tsa/main"
# 'docker images' should print image smaller than 8mb
```

# Create postgres user and permission

```sql
-- Create user
CREATE USER twitch_stream_announcer WITH PASSWORD 'your_password';
-- Add select permission
GRANT SELECT ON stream_announcer_streams TO twitch_stream_announcer;
--Add update permission to columns status and announced_at
GRANT UPDATE(status, announced_at) ON stream_announcer_streams TO twitch_stream_announcer;
```

---

## Architecture

```mermaid
flowchart TD
    subgraph External_APIs[External Services]
        Twitch_API[Twitch Helix API]
        Discord_Webhook[Discord Webhooks]
        Postgres[(PostgreSQL<br/>stream_announcer_streams)]
    end

    subgraph Application
        main[main proc]
        run_once[run_once proc]
        fetch_users[fetch_postgres_users]
        fetch_twitch[fetch_twitch_stream_status]
        decide[get_which_streams...]
        update_db[update_database_entries]
        send_webhooks[send_webhooks]
    end

    main --> decide_mode{STAGE mode?}
    decide_mode -->|DEV| run_once
    decide_mode -->|PROD| run_for_one_hour
    run_for_one_hour --> run_once

    run_once --> fetch_users
    run_once --> fetch_twitch
    run_once --> decide
    run_once --> update_db
    run_once --> send_webhooks

    fetch_users --> Postgres
    fetch_twitch --> Twitch_API
    decide --> decide_to_announce{Should<br/>announce?}
    decide_to_announce -->|Yes| send_webhooks
    send_webhooks --> Discord_Webhook
```

```mermaid
flowchart TD
    Start[Check Stream] --> Is_Live{Stream live?}

    Is_Live -->|No| Was_Online{Was online<br/>before?}
    Was_Online -->|Yes| Mark_Offline[Mark as offline]
    Was_Online -->|No| Skip1[Skip]

    Is_Live -->|Yes| Update_Online[Update online status]
    Update_Online --> Was_Offline{Was offline?}

    Was_Offline -->|No| Skip2[Skip]
    Was_Offline -->|Yes| Check_Time{Last seen<br/>> 30 min ago?}

    Check_Time -->|No| Skip3[Skip - probably<br/>reconnected]
    Check_Time -->|Yes| Announce[Add to<br/>announce list]
```

```mermaid
sequenceDiagram
    participant DB as PostgreSQL
    participant App as twitch_stream_announcer
    participant Twitch as Twitch Helix API
    participant Discord as Discord Webhooks

    App->>DB: SELECT enabled streams
    DB-->>App: List of monitored streamers

    App->>Twitch: OAuth2 client credentials<br/>get access token
    Twitch-->>App: Access token

    App->>Twitch: GET /helix/streams<br/>for all streamer names
    Twitch-->>App: Stream status data

    App->>App: Compare with DB state

    alt Stream came online after 30+ min offline
        App->>DB: UPDATE status='online'<br/>announced_at=NOW()
        App->>Discord: POST webhook<br/>rich embed with stream info
        Discord-->>App: 204 No Content
    else Stream went offline
        App->>DB: UPDATE status='offline'
    else Stream still online
        App->>DB: UPDATE status='online'
    end
```

```mermaid
erDiagram
    STREAM_ANNOUNCER_STREAMS {
        int id PK
        text twitch_name
        text discord_webhook
        text announce_message
        timestamptz announced_at
        text status
        timestamptz last_seen_online
        bool enabled
    }
```
