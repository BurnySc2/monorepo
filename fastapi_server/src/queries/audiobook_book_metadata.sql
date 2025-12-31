-- Query needs to provide information on:
-- Do all chapters have generated audio? ("Download audiobook" button)
-- Number of chapters that are queued + generating + generated ("Delete audio of all chapters" button)
-- Number of chapters that have no conversion pending ("Generate audio for all chapters" button)
-- Info about the book: book_id, book_name, book_author

-- If count larger than 0, then display "Delete audio of all chapters" button
-- If count not equal to total chapter count, then display "Generate audio for all chapters" button
WITH chapters_may_have_audio AS (
    SELECT COUNT(*) AS count
    FROM litestar_audiobook_chapter AS c
    WHERE
        c.book = { }
        AND
        (
            c.queued IS NOT NULL
            OR c.started_converting IS NOT NULL
            OR c.minio_object_name IS NOT NULL
        )
),

-- If count equal to total chapter count, then display "Download audiobook" button
chapters_have_audio_generated AS (
    SELECT COUNT(*) AS count
    FROM litestar_audiobook_chapter AS c
    WHERE
        c.book = { }
        AND c.minio_object_name IS NOT NULL
)

SELECT
    b.id AS book_id,
    b.book_title,
    b.book_author,
    b.chapter_count,
    cmha.count <> b.chapter_count AS show_button_generate_all_audio,
    0 < cmha.count AS show_button_delete_all_audio,
    chag.count = b.chapter_count AS show_button_download_book
FROM
    litestar_audiobook_book AS b
CROSS JOIN chapters_may_have_audio AS cmha
CROSS JOIN chapters_have_audio_generated AS chag
WHERE b.id = { } AND b.deleted = FALSE
ORDER BY b.id
LIMIT 1
