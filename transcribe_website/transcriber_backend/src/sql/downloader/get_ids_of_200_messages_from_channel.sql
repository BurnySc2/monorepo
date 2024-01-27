SELECT message_id FROM telegram_messages_to_download
WHERE download_status = 'QUEUED' AND channel_id = %(message_channel_id)s
ORDER BY file_size_bytes DESC
LIMIT 200
