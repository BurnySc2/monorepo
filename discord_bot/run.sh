docker build -t discord_bot_image .
docker run  --rm --name discord_bot \
  --mount type=bind,source="$(pwd)/data",destination=/root/discord_bot/data \
  --mount type=bind,source="$(pwd)/DISCORDKEY",destination=/root/discord_bot/DISCORDKEY,readonly \
  discord_bot_image
