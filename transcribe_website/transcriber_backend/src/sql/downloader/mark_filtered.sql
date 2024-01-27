UPDATE telegram_messages_to_download SET download_status = %(queued)s WHERE
    NOT (download_status = ANY(%(status)s::text []))
    AND file_unique_id != ''
    AND
    (
        (
            media_type = 'Photo' AND %(accept_photo)s
            AND %(photo_min_file_size_bytes)s <= file_size_bytes
            AND file_size_bytes <= %(photo_max_file_size_bytes)s
        )
        OR
        (
            media_type = 'Video' AND %(accept_video)s
            AND %(video_min_file_size_bytes)s <= file_size_bytes
            AND file_size_bytes <= %(video_max_file_size_bytes)s
            AND %(video_min_file_duration_seconds)s <= file_duration_seconds
            AND file_duration_seconds <= %(video_max_file_duration_seconds)s
        )
        OR
        (
            media_type = 'Audio' AND %(accept_audio)s
            AND %(audio_min_file_size_bytes)s <= file_size_bytes
            AND file_size_bytes <= %(audio_max_file_size_bytes)s
            AND %(audio_min_file_duration_seconds)s <= file_duration_seconds
            AND file_duration_seconds <= %(audio_max_file_duration_seconds)s
        )
    );
