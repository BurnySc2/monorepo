# Transcriber Service

## Prerequisites

- Python >= 3.10 <3.14 (pony doesn't support 3.11 yet)
- (Optional) Docker

Install

```sh
pip install --user uv
uv sync
```

## Transcribe
Get the text from a video or audio file
```sh
transcribe_file.py:transcribe_file
```

Save transcribe result to database
```sh
transcribe_file.py:save_result_to_db
```

Mass transcribe files from a given folder and save to database
```sh
transcribe_file.py:mass_transcribe
```

## Create subtitles

