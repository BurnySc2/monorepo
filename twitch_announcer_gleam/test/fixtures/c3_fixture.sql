-- C3 smoke fixture: stream_announcer_streams rows for db contract tests.
CREATE TABLE IF NOT EXISTS stream_announcer_streams (
  id serial PRIMARY KEY,
  twitch_name text NOT NULL,
  discord_webhook text NOT NULL,
  announce_message text NOT NULL,
  announced_at timestamptz,
  status text NOT NULL,
  last_seen_online timestamptz,
  enabled boolean NOT NULL DEFAULT TRUE
);
DELETE FROM stream_announcer_streams
WHERE twitch_name IN ('c3_smoke_alice', 'c3_smoke_disabled');
INSERT INTO stream_announcer_streams
  (twitch_name, discord_webhook, announce_message, announced_at, status, last_seen_online, enabled)
VALUES
  ('c3_smoke_alice', 'https://example.invalid/c3', '@here alice live', NULL, 'offline', NULL, TRUE),
  ('c3_smoke_disabled', 'https://example.invalid/c3', '@here bob live', NULL, 'offline', NULL, FALSE);
