UPDATE telegram_messages_to_download
SET download_status = %(new_status)s
WHERE
    download_status = 'QUEUED'
    AND channel_id = %(my_channel_id)s
    AND message_id = ANY(%(message_ids)s)
