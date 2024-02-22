SELECT COUNT(*) FROM telegram_messages_to_download
WHERE
    file_unique_id = %(my_file_unique_id)s
    AND download_status = 'COMPLETED'
