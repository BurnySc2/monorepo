# Prerequisites
- Python >= 3.8 <3.11
- (Optional) Docker

Copy the `SECRETS.example.toml` to `SECRETS.toml` and fill out your secrets.

# Enqueue Worker
`poetry run python enqueue_jobs.py`

# Processing Worker
The docker processes all jobs with the faster_whisper model.

`poetry run python worker.py`

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
