UPDATE telegram_messages_to_download SET download_status = %(status)s
WHERE download_status = ANY(%(queued_or_downloading)s::text []);
