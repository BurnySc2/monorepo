FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base

# Add ffmpeg from
# https://github.com/wader/static-ffmpeg
COPY --from=mwader/static-ffmpeg:7.1 /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:7.1 /ffprobe /usr/local/bin/

WORKDIR /app

# Install dependencies
COPY uv.lock pyproject.toml ./
RUN uv sync --no-dev --frozen --no-cache --no-install-project

COPY src src

# Allow imports to function correctly
ENV PYTHONPATH=/app

ENTRYPOINT [ "uv", "run", "--no-dev", "python", "src/worker.py" ]
