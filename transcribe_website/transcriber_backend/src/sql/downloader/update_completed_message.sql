UPDATE telegram_messages_to_download
SET
    download_status = %(new_status)s,
    downloaded_file_path = %(downloaded_file_path)s,
    extracted_mp3_size_bytes = %(extracted_mp3_size_bytes)s
WHERE
    channel_id = %(my_channel_id)s
    AND message_id = %(message_id)s
