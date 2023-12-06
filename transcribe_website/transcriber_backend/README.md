# Transcriber Service
## Prerequisites
- Python >= 3.8 <3.11 (pony doesn't support 3.11 yet)
- Postgres server (or modify `src/db.py` to connect to local sqlite)
- (Optional) Docker

Copy the `SECRETS.example.toml` to `SECRETS.toml` and fill out your secrets.

Install
```sh
pip install --user poetry
poetry install
```

## Enqueue Worker
Configure the `SECRETS.toml` accordingly to match the files you want to upload to be enqueued in transcription.

`PYTHONPATH=$(pwd) poetry run python src/enqueue_jobs.py`

or with limited bandwidth via [trickle](https://github.com/mariusae/trickle)

`PYTHONPATH=$(pwd) trickle -d 10000 -u 800 poetry run python src/enqueue_jobs.py`

or containerized via docker (don't forget to set your upload path correctly)

```sh
docker build -t transcribe_worker .
docker run --rm \
    --name enqueue_worker \
    -v ./SECRETS.toml:/app/SECRETS.toml:ro \
    -v ./download_path:/app/download_path \
    --entrypoint poetry \
    transcribe_worker \
    run python src/enqueue_jobs.py
```

## Processing Worker
The docker processes all jobs with the faster_whisper model.

`PYTHONPATH=$(pwd) poetry run python src/worker.py`

or containerized via docker

```sh
docker build -t transcribe_worker .
docker run --rm \
    --name transcribe_worker \
    -v ./SECRETS.toml:/app/SECRETS.toml:ro \
    -v ./whisper_models:/app/whisper_models \
    transcribe_worker
```
Debugging container:
`docker run --rm -it --entrypoint bash transcribe_worker`

# Telegram Media Downloader
Inspired by https://github.com/Dineshkarthik/telegram_media_downloader to download media from telegram.

## Use case
The telegram desktop client already supports "export chat history" but only downloads one by one files and if ran multiple times, it redownloads all files instead of skipping already downloaded files. You have no way of filtering messages (except for by type), and you can only download messages from one channel at a time.

This tool aims to fix that by
- downloading from multiple channels
- downloading multiple files at a time
- skip already downloaded files
- filter
    - by file size
    - by duration (audio and video)

## Usage
Prerequisite:
- Python >= 3.8 <3.11 (pony doesn't support 3.11 yet)
- Postgres server (or modify `src/db.py` to connect to local sqlite)
- A telegram account
- (Optional) ffmpeg (to extract mp3 from video files to transcribe)

Copy the `SECRETS.example.toml` to `SECRETS.toml` and adjust the parameters.

Get your API keys from https://my.telegram.org/apps
```sh
pip install --user poetry
poetry install
PYTHONPATH=$(pwd) poetry run python src/telegram_downloader.py
```

or containerized via docker (don't forget to set your download path correctly)

```sh
docker build -t transcribe_worker .
docker run --rm \
    --name telegram_downloader \
    -v ./SECRETS.toml:/app/SECRETS.toml:ro \
    -v ./download_path:/app/download_path \
    -v ./media_downloader.session:/app/media_downloader.session \
    --entrypoint poetry \
    transcribe_worker \
    run python src/telegram_downloader.py
```