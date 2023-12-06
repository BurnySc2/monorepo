set -e
docker build -t discord_bot_image .
docker run --rm --name discord_bot --env STAGE=DEV \
  --mount type=bind,source="$(pwd)/data",destination=/root/discord_bot/data \
  --mount type=bind,source="$(pwd)/SECRETS.toml",destination=/root/discord_bot/SECRETS.toml,readonly \
  discord_bot_image
