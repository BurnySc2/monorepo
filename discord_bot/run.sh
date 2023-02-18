docker build -t discord_bot_image .
docker run --rm --name discord_bot --env STAGE=DEV \
  --mount type=bind,source="$(pwd)/data",destination=/root/discord_bot/data \
  --mount type=bind,source="$(pwd)/DISCORDKEY",destination=/root/discord_bot/DISCORDKEY,readonly \
  --mount type=bind,source="$(pwd)/SUPABASEURL",destination=/root/discord_bot/SUPABASEURL,readonly \
  --mount type=bind,source="$(pwd)/SUPABASEKEY",destination=/root/discord_bot/SUPABASEKEY,readonly \
  discord_bot_image
