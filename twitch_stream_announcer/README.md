# Create postgres user and permission

```sql
-- Create user
CREATE USER twitch_stream_announcer WITH PASSWORD 'your_password';
-- Add select permission
GRANT SELECT ON stream_announcer_streams TO twitch_stream_announcer;
--Add update permission to columns status and announced_at
GRANT UPDATE(status, announced_at) ON stream_announcer_streams TO twitch_stream_announcer;
```
