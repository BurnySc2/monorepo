-- Count queued transcriptions
SELECT COUNT(*) FROM transcribe_jobs
WHERE status <> 'DONE';

-- Sum of file sizes of queued transcriptions
SELECT SUM(input_file_size_bytes) FROM transcribe_jobs
WHERE status IN ('QUEUED', 'ACCEPTED', 'PROCESSING');

-- Select files with no link and show total mp3 size
SELECT SUM(extracted_mp3_size_bytes) FROM telegram_messages_to_download
WHERE linked_transcription IS NULL AND extracted_mp3_size_bytes IS NOT NULL;

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

-- Find duplicates in transcribe_jobs table
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
	WHERE linked_transcription IS NULL
)

SELECT * FROM transcribe_jobs
WHERE id IN (SELECT linked_transcription FROM temp);

-- Reset all completed downloads which have no link
UPDATE telegram_messages_to_download
SET downloaded_file_path = NULL, 
	extracted_mp3_size_bytes = NULL,
	download_status = 'FILTERED'
WHERE linked_transcription IS NULL 
AND download_status = 'COMPLETED'
AND downloaded_file_path IS NOT NULL;

-- Get all transcribe jobs which have a mp3 file
WITH temp AS (
	SELECT job_item
	FROM transcribe_mp3s 
)

SELECT * FROM transcribe_jobs
WHERE id IN (SELECT job_item FROM temp)
ORDER BY input_file_size_bytes DESC

-- Delete all mp3s where transcribe jobs that have AV_ERROR
WITH temp AS (
	SELECT id
	FROM transcribe_jobs 
	WHERE status = 'AV_ERROR'
)

DELETE FROM transcribe_mp3s
WHERE job_item IN (SELECT id FROM temp);
