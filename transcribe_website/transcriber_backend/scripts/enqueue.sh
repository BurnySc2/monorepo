docker run --rm \
    --name enqueue_worker \
    -v ./SECRETS.toml:/app/SECRETS.toml:ro \
    -v ./downloads:/downloads \
    --entrypoint poetry \
    burnysc2/transcribe_worker:latest \
    run python src/enqueue_jobs.py
