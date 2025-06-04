FROM ghcr.io/astral-sh/uv:python3.12-alpine AS base

# Install dependencies
COPY uv.lock pyproject.toml /root/discord_bot/

WORKDIR /root/discord_bot
RUN uv sync --no-dev --frozen --no-cache --no-install-project

COPY src /root/discord_bot/src

RUN rm -r \
    /var/cache

# Squash image with trick https://stackoverflow.com/a/56118557/10882657
FROM scratch
COPY --from=base / /
WORKDIR /root/discord_bot
ENV PYTHONPATH=$PYTHONPATH:/root/discord_bot/src
CMD ["uv", "run", "--no-dev", "src/discord_bot.py"]
