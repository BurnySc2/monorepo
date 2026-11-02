-- Idempotent create-or-repair of the Telegram indexes. Keep as one statement:
-- asyncpg prepares each statement and rejects ';'-separated commands. No
-- CONCURRENTLY (rejected in a transaction / DO block), no VACUUM, no ANALYZE.
DO $do$
DECLARE
    spec record;
BEGIN
    FOR spec IN
        SELECT *
        FROM (VALUES
            ('litestar_telegram_message_channel_message_id_uq', 'litestar_telegram_message',
             true, ARRAY['channel', 'message_id']::text[], NULL::text),
            ('litestar_telegram_download_queued_idx', 'litestar_telegram_download',
             false, ARRAY['download_queue_time']::text[], $q$(status = 'Queued'::text)$q$)
        ) AS t(name, tbl, is_unique, cols, pred)
    LOOP
        -- Serializes concurrent starters (uvicorn workers, parser + api); released at commit.
        PERFORM pg_advisory_xact_lock(hashtext(spec.name));

        -- Skip when an index of this exact shape already exists and is valid.
        -- Checks column identity and order (indkey), uniqueness, partiality,
        -- predicate, and that it is not an expression index.
        CONTINUE WHEN EXISTS (
            SELECT 1
            FROM pg_index i
            WHERE i.indexrelid = to_regclass('public.' || spec.name)
              AND i.indrelid = to_regclass('public.' || spec.tbl)
              AND i.indisvalid
              AND i.indisunique = spec.is_unique
              AND i.indexprs IS NULL
              AND pg_get_expr(i.indpred, i.indrelid) IS NOT DISTINCT FROM spec.pred
              AND ARRAY(SELECT unnest(i.indkey::int2[])) = (
                  SELECT array_agg(a.attnum ORDER BY c.ord)
                  FROM unnest(spec.cols) WITH ORDINALITY AS c(col, ord)
                  JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attname = c.col
              )
        );

        -- Same name but not an index on the target table: refuse instead of dropping it.
        IF to_regclass('public.' || spec.name) IS NOT NULL AND NOT EXISTS (
            SELECT 1
            FROM pg_index i
            WHERE i.indexrelid = to_regclass('public.' || spec.name)
              AND i.indrelid = to_regclass('public.' || spec.tbl)
        ) THEN
            RAISE EXCEPTION USING MESSAGE =
                format('public.%I exists but is not an index on public.%I; refusing to drop it',
                       spec.name, spec.tbl);
        END IF;

        -- Never DROP a constraint-owned index: Postgres raises 2BP01 and startup dies.
        IF EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conindid = to_regclass('public.' || spec.name)) THEN
            RAISE EXCEPTION USING MESSAGE =
                format('Index %s exists but does not match (%s) and is owned by a constraint; '
                       'fix that constraint instead', spec.name, array_to_string(spec.cols, ', '));
        END IF;

        -- Fail with a readable message instead of a bare UniqueViolationError.
        IF spec.is_unique AND EXISTS (
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

        EXECUTE format('DROP INDEX IF EXISTS public.%I', spec.name);
        EXECUTE format(
            'CREATE %sINDEX %I ON public.%I USING btree (%s)%s',
            CASE WHEN spec.is_unique THEN 'UNIQUE ' ELSE '' END,
            spec.name, spec.tbl, array_to_string(spec.cols, ', '),
            coalesce(' WHERE ' || spec.pred, '')
        );
    END LOOP;
END
$do$;
