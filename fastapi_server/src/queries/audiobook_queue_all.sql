UPDATE litestar_audiobook_chapter
SET
    audio_settings = $2::jsonb,
    queued = NOW()
WHERE
    book_id = $1
    AND queued IS NULL
RETURNING chapter_number;
