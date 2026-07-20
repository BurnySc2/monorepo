SELECT
    c.channel_title,
    c.channel_username,
    c.creation_date,
    c.participants,
    COUNT(m.id) AS total_messages,
    COUNT(m.id) FILTER (WHERE m.status != 'NoFile') AS total_files
FROM litestar_telegram_channel AS c
LEFT JOIN litestar_telegram_message AS m ON c.channel_id = m.channel
GROUP BY c.channel_id, c.channel_title, c.channel_username, c.creation_date, c.participants
ORDER BY total_messages DESC
