-- Count queued transcriptions
SELECT COUNT(*) FROM transcribe_jobs
WHERE status <> 'DONE';

-- Find all duplicate files in the database based on file size and duration
SELECT file_size_bytes, file_duration_seconds, COUNT(*)
FROM telegram_messages_to_download
GROUP BY file_size_bytes, file_duration_seconds
HAVING COUNT(*) > 1
ORDER BY file_size_bytes;

-- Find duplicates based on file path
SELECT downloaded_file_path
FROM telegram_messages_to_download 
WHERE downloaded_file_path <> ''
GROUP BY downloaded_file_path
HAVING COUNT(*) > 1
ORDER BY downloaded_file_path

-- Find duplicates in trascribe_jobs table
SELECT local_file
FROM transcribe_jobs
WHERE local_file <> ''
GROUP BY local_file
HAVING COUNT(*) > 1
ORDER BY local_file;

-- Find more info on the duplicates using CTE
WITH temp AS (
	SELECT downloaded_file_path
	FROM telegram_messages_to_download 
	WHERE downloaded_file_path <> ''
	GROUP BY downloaded_file_path
	HAVING COUNT(*) > 1
	ORDER BY downloaded_file_path
)

SELECT * FROM telegram_messages_to_download
WHERE downloaded_file_path IN (SELECT downloaded_file_path FROM temp)
ORDER BY downloaded_file_path;

-- Select transcriptions with no link
WITH temp AS (
	SELECT linked_transcription
	FROM telegram_messages_to_download 
	WHERE linked_transcription IS NOT NULL
)

SELECT * FROM transcribe_jobs
WHERE id IN (SELECT linked_transcription FROM temp);
