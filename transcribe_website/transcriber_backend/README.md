# Transcriber Service
## Prerequisites
- Python >= 3.8 <3.11 (pony doesn't support 3.11 yet)
- Postgres server (or modify `src/db.py` to connect to local sqlite)
- (Optional) Docker

Copy the `SECRETS.example.toml` to `SECRETS.toml` and fill out your secrets.

Install
```
pip install --user poetry
poetry install
```

## Enqueue Worker
Configure the `SECRETS.toml` accordingly to match the files you want to upload to be enqueued in transcription.

`poetry run python src/enqueue_jobs.py`

## Processing Worker
The docker processes all jobs with the faster_whisper model.

`poetry run python src/worker.py`

or containerized via docker

```
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

Copy the `SECRETS.example.toml` to `SECRETS.toml` and adjust the parameters.

Get your API keys from https://my.telegram.org/apps
```
pip install --user poetry
poetry install
poetry run python src/telegram_downloader.py
```
