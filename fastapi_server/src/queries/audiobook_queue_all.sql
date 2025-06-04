UPDATE litestar_audiobook_chapter
SET
    audio_settings = { }::jsonb,
    queued = NOW()
WHERE
    book = { }
    AND queued IS NULL
    AND minio_object_name IS NULL
RETURNING chapter_number;
