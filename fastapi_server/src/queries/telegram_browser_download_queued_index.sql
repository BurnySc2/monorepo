DO $do$
BEGIN
    -- Reboot path: a valid index already exists, do nothing.
    IF NOT EXISTS (
        SELECT 1
        FROM pg_index
        WHERE indexrelid = to_regclass('public.litestar_telegram_download_queued_idx')
          AND indrelid = 'public.litestar_telegram_download'::regclass
          AND indisvalid
    ) THEN
        -- (a) Remove a leftover invalid index so CREATE ... IF NOT EXISTS does not skip it.
        IF EXISTS (
            SELECT 1
            FROM pg_index
            WHERE indexrelid = to_regclass('public.litestar_telegram_download_queued_idx')
              AND indrelid = 'public.litestar_telegram_download'::regclass
              AND NOT indisvalid
        ) THEN
            EXECUTE 'DROP INDEX IF EXISTS public.litestar_telegram_download_queued_idx';
        END IF;

        -- (b) Build the partial index for the downloader queue poll.
        EXECUTE $ddl$CREATE INDEX IF NOT EXISTS litestar_telegram_download_queued_idx
ON public.litestar_telegram_download (download_queue_time)
WHERE status = 'Queued'$ddl$;
    END IF;
END
$do$;
