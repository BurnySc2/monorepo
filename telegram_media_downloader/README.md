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
- A telegram account
- Python 3.8 or newer

Copy the `SECRETS.example.toml` to `SECRETS.toml` and adjust the parameters.

To get your API keys open https://my.telegram.org/apps
```
pip install --user poetry
poetry install
poetry run python main.py
```
