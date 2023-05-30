# Frontend
- allow login with account (twitch, github, google, email)
- allow log out
- allow user to queue new job
    - if file was video file, use ffmpeg to convert to mp3 before uploading https://github.com/ffmpegwasm/ffmpeg.wasm
    - after upload is completed: enqueue job to supabase
- allow user to see progress of job
- allow user to see output of completed jobs (on success / fail)
- limit user (x jobs in 24h, n jobs in queue)


# Backend
https://github.com/ahmetoner/whisper-asr-webservice

- frequently check if new jobs are available
- if any worker idle (active_workers < max_worker_count):
    - fetch jobs from supabase
        - mark jobs as fail if retry >= max_retry
        - mark jobs as stale if job_started time has been too long ago
    - start job and update progress to supabase https://github.com/openai/whisper/discussions/850#discussioncomment-5443424
    - on finish: upload all output files as database row entry? or as zip
    - on failure: retry if recoverable fail


# Backend - Mass transcribe
- for all video (and audio) files create a ffmpeg extract audio job
- worker
    - filter
        - filesize 1mb < X < 100mb
        - via ffprobe: 5s < duration < 5m
    - extract mp3 from video
    - upload to supabase
    - enqueue job in queue
- on success (check supabase)
    - download .txt and .srt file and put them in respective folders
    - (optional) remove related/extracted .mp3 file


# Supabase table schema
| Field Name         | Data Type | Example |
|--------------------|-----------|---------|
| id                 |   int     | 1 |
| user name          |   str        | burny |
| job_added datetime |   datetime        | today 0:00 |
| job_started datetime |   null/datetime       | null |
| retry              |   int     | 3
| max retries        |   int     | 5
| status        |   str     | completed |
| input_data          | point to data bucket | my_file.mp3
| output_data          | null / blob (zip of output) |
| job_params | json | which model (tiny, small, medium), transcribe/translate, language (en, de)

