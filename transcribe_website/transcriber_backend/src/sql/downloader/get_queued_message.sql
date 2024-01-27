SELECT * FROM telegram_messages_to_download
WHERE download_status = 'QUEUED'
ORDER BY channel_id ASC, message_date DESC
LIMIT %(my_limit)s
