SELECT
    (
        SELECT COUNT(*) FROM telegram_messages_to_download WHERE download_status = ANY(%(done_status)s::text [])
    ) AS done_count,
    (
        SELECT COUNT(*) FROM telegram_messages_to_download WHERE download_status = ANY(%(total_status)s::text [])
    ) AS total_count,
    (
        SELECT SUM(file_size_bytes)
        FROM telegram_messages_to_download
        WHERE download_status = ANY(%(done_status)s::text [])
    ) AS done_bytes,
    (
        SELECT SUM(file_size_bytes)
        FROM telegram_messages_to_download
        WHERE download_status = ANY(%(total_status)s::text [])
    ) AS total_bytes
