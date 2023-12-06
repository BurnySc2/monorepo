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
        - start by launching a docker container
        - docker container only has access to mp3 file and an output directory for the resulting files
        - docker has volume with whisper models
    - on finish: upload all output files as database row entry? or as zip
    - on failure: retry if recoverable fail

# Dockerfile
- image with faster_whisper but no models installed
- models will be downloaded (and cached in volume) on container launch
- endpoints
    - detect language
    - transcribe (+ translate) with params:
        - autodetect or force language detection
        - transcribe or translate (to english)


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
| issued_user          |   str        | burny |
| job_created datetime |   datetime        | today 0:00 |
| job_started datetime |   null/datetime       | null |
| job_completed datetime |   null/datetime       | null |
| retry              |   int     | 2
| max retries        |   int     | 3
| status        |   str     | 55% completed |
| output_data          | null / blob (zip of output) |
| job_params | json | which model (tiny, small, medium), transcribe/translate, language (en, de)

