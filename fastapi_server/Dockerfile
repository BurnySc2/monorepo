# Manually build with:
# docker build -t burnysc2/litestar_server:latest_dev .
# Interactively run with
# docker run --rm -it burnysc2/litestar_server:latest_dev /bin/sh
# docker run --rm -it burnysc2/litestar_server:latest_dev /bin/sh -c "apk add gdu && gdu /"
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS base

# Add ffmpeg from
# https://github.com/wader/static-ffmpeg
# COPY --from=mwader/static-ffmpeg:7.1 /ffmpeg /usr/local/bin/
# COPY --from=mwader/static-ffmpeg:7.1 /ffprobe /usr/local/bin/

WORKDIR /root/fastapi_server

# Install dependencies
COPY uv.lock pyproject.toml ./

RUN uv sync --no-dev --frozen --no-cache --no-install-project

COPY src src

RUN rm -r \
    /var/cache

# Squash image with trick https://stackoverflow.com/a/56118557/10882657
FROM scratch
COPY --from=base / /
WORKDIR /root/fastapi_server
ENV PYTHONPATH=$PYTHONPATH:/root/fastapi_server/src
CMD ["uv", "run", "--no-dev", "--directory", "src", "rio", "run", "--port", "8000", "--release", "--public"]
