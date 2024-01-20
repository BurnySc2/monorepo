# May be executed with
# nohup sh start_dl.sh &
docker run --rm \
    --name telegram_downloader \
    -v ./SECRETS.toml:/app/SECRETS.toml:ro \
    -v ./downloads:/downloads \
    -v ./media_downloader.session:/app/media_downloader.session \
    --entrypoint poetry \
    burnysc2/transcribe_worker:latest \
    run python src/telegram_downloader.py
