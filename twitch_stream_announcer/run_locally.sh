# Build image locally
docker build -t burnysc2/twitch_stream_announcer:latest .
# Start container and attach to logs
docker compose up
