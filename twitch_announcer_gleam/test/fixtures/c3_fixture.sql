-- C3 smoke fixture: stream_announcer_streams rows for db contract tests.
CREATE TABLE IF NOT EXISTS stream_announcer_streams (
  id bigint NOT NULL PRIMARY KEY,
  created_at timestamp NULL,
  enabled boolean NOT NULL DEFAULT true,
  twitch_name varchar NULL,
  discord_webhook varchar NULL,
  announce_message varchar NULL,
  announced_at timestamp NOT NULL DEFAULT '1970-01-01 00:00:00',
  status text NULL,
  last_seen_online timestamp NOT NULL DEFAULT '1970-01-01 00:00:00'
);
DELETE FROM stream_announcer_streams WHERE twitch_name LIKE 'c3_%';
INSERT INTO stream_announcer_streams
  (id, twitch_name, discord_webhook, announce_message, announced_at, status, last_seen_online, enabled)
VALUES
  (9001, 'c3_smoke_alice', 'https://example.invalid/c3', '@here alice live', '1970-01-01 00:00:00', 'offline', '1970-01-01 00:00:00', TRUE),
  (9002, 'c3_smoke_disabled', 'https://example.invalid/c3', '@here bob live', '1970-01-01 00:00:00', 'offline', '1970-01-01 00:00:00', FALSE);
