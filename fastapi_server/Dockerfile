# Manually build with:
# docker build -t burnysc2/litestar_server:latest_dev .
# Interactively run with
# docker run --rm -it burnysc2/litestar_server:latest_dev /bin/sh
# docker run --rm -it burnysc2/litestar_server:latest_dev /bin/sh -c "apk add gdu && gdu /"
FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS base

# Required by tts engines like kokoro
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Add ffmpeg from
# https://github.com/wader/static-ffmpeg
COPY --from=mwader/static-ffmpeg:8.1.1 /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:8.1.1 /ffprobe /usr/local/bin/

WORKDIR /root/fastapi_server

# Install dependencies
COPY uv.lock pyproject.toml ./

RUN uv sync --no-dev --frozen --no-cache --no-install-project

COPY src src

# Squash image with trick https://stackoverflow.com/a/56118557/10882657
FROM scratch
COPY --from=base / /
WORKDIR /root/fastapi_server
ENV PYTHONPATH=$PYTHONPATH:/root/fastapi_server/src
CMD ["uv", "run", "--no-dev", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
