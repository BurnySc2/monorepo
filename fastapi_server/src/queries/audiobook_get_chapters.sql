-- TODO Create class from pydantic BaseModel that matches the result of the select query

-- Goal of the query is retrieve all data for the initial page load
-- If a chapter is queued for conversion to audio, then it needs to be retrieved what position in the queue it is

-- Retrieve all chapters that are queued and conversion hasn't started
WITH all_queued AS (
    SELECT
        c.id,
        -- TODO Verify this number starts with 1
        ROW_NUMBER() OVER (
            ORDER BY c.queued ASC, c.chapter_number ASC
        ) AS number_in_queue
    FROM
        litestar_audiobook_chapter AS c
    WHERE
        c.queued IS NOT NULL
        AND c.started_converting IS NULL
        AND c.minio_object_name IS NULL
)

-- Then filter out those chapters that do not belong to the book while keeping the number_in_queued information
SELECT
    c.id,
    c.book AS book_id,
    -- Will be either a number if queued, or NULL if not yet queued, started converting or done converting
    q.number_in_queue,
    c.chapter_title,
    c.chapter_number,
    c.word_count,
    c.sentence_count,
    -- Should presigned minio urls be generated on page load or only on demand when the user clicks "load audio"?
    c.minio_object_name,
    -- If a chapter is currently converting, show "generating audio"
    c.started_converting IS NOT NULL AS is_converting,
    -- If a chapter has a minio_object_name, the conversion is complete
    c.minio_object_name IS NOT NULL AS has_audio
FROM
    litestar_audiobook_chapter AS c
LEFT JOIN all_queued AS q
    ON c.id = q.id
LEFT JOIN litestar_audiobook_book AS b
    ON c.book = b.id
WHERE
    c.book = { }
    AND c.chapter_number = ANY(CAST({ } AS INTEGER []))
    AND b.deleted = FALSE
ORDER BY c.chapter_number ASC
