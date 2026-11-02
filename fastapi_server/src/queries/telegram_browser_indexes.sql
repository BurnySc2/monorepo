-- Idempotent. One statement only: asyncpg prepares it and rejects
-- ';'-separated commands. No CONCURRENTLY (cannot run in a transaction),
-- no VACUUM, no ANALYZE.
-- IF NOT EXISTS matches by name only: an existing index with a different
-- shape, or an invalid one, is kept as-is and not repaired.
CREATE INDEX IF NOT EXISTS litestar_telegram_download_queued_idx
ON public.litestar_telegram_download (download_queue_time)
WHERE status = 'Queued';
