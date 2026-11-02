DO $do$
BEGIN
    -- Reboot path: a valid index already exists, do nothing.
    IF NOT EXISTS (
        SELECT 1
        FROM pg_index
        WHERE indexrelid = to_regclass('public.litestar_telegram_message_channel_message_id_uq')
          AND indrelid = 'public.litestar_telegram_message'::regclass
          AND indisunique
          AND indisvalid
    ) THEN
        -- (a) Refuse to start on duplicate (channel, message_id) pairs.
        IF EXISTS (
            SELECT 1
            FROM public.litestar_telegram_message
            WHERE channel IS NOT NULL
            GROUP BY channel, message_id
            HAVING count(*) > 1
        ) THEN
            RAISE EXCEPTION USING MESSAGE =
                'Cannot create unique index litestar_telegram_message_channel_message_id_uq: '
                || 'duplicate (channel, message_id) pairs exist in public.litestar_telegram_message; '
                || 'de-duplicate these rows before starting the server';
        END IF;

        -- (b) Remove a leftover invalid index so CREATE ... IF NOT EXISTS does not skip it.
        IF EXISTS (
            SELECT 1
            FROM pg_index
            WHERE indexrelid = to_regclass('public.litestar_telegram_message_channel_message_id_uq')
              AND indrelid = 'public.litestar_telegram_message'::regclass
              AND NOT indisvalid
        ) THEN
            EXECUTE 'DROP INDEX IF EXISTS public.litestar_telegram_message_channel_message_id_uq';
        END IF;

        -- (c) Build the index. Index name unqualified, table schema-qualified.
        EXECUTE $ddl$CREATE UNIQUE INDEX IF NOT EXISTS litestar_telegram_message_channel_message_id_uq
ON public.litestar_telegram_message (channel, message_id)$ddl$;
    END IF;
END
$do$;
