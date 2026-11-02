-- Idempotent. One statement only: asyncpg prepares it and rejects
-- ';'-separated commands. No CONCURRENTLY (cannot run in a transaction),
-- no VACUUM, no ANALYZE.
-- IF NOT EXISTS matches by name only: an existing index with a different
-- shape, or an invalid one, is kept as-is and not repaired.
CREATE UNIQUE INDEX IF NOT EXISTS litestar_telegram_message_channel_message_id_uq
ON public.litestar_telegram_message (channel, message_id);
