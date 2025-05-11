# Manually build with:
# docker build -t burnysc2/litestar_server:latest_dev .
# Interactively run with
# docker run --rm -it burnysc2/litestar_server:latest_dev /bin/sh
# docker run --rm -it burnysc2/litestar_server:latest_dev /bin/sh -c "apk add gdu && gdu /"
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS base

# Install npm for prisma
RUN apk add --no-cache npm

# Add ffmpeg from
# https://github.com/wader/static-ffmpeg
COPY --from=mwader/static-ffmpeg:7.1 /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:7.1 /ffprobe /usr/local/bin/

# Install dependencies
COPY uv.lock pyproject.toml /root/fastapi_server/

WORKDIR /root/fastapi_server
RUN uv sync --no-dev --frozen --no-cache --no-install-project
# See https://github.com/astral-sh/uv-docker-example/blob/main/Dockerfile
ENV PATH="/root/fastapi_server/.venv/bin:$PATH"
RUN rm uv.lock pyproject.toml

# Sanity check if prisma works
RUN prisma -v

# Prepare prisma client and generate types
COPY prisma /root/fastapi_server/prisma
RUN prisma generate

COPY src /root/fastapi_server/src

RUN rm -r \
    /usr/bin/node \
    /usr/lib/node_modules \
    /root/.npm \
    /root/.cache/prisma \
    # Required for interaction with prisma: /root/.cache/prisma-python \
    /var/cache

# https://stackoverflow.com/a/52638888
# Remove unused packages in /root/fastapi_server/.venv/lib/python3.12/site-packages/
RUN SITE_PACKAGES=$(python -c "import sysconfig; print(sysconfig.get_path('purelib'))") \
    && echo $SITE_PACKAGES \
    && rm -r \
    $SITE_PACKAGES/faker \
    $SITE_PACKAGES/pygments

# Remove 30mb uv binary
RUN rm /usr/local/bin/uv

# Remove unused packages in /usr/local/lib/python3.12
RUN PYTHON_LIB=$(/usr/local/bin/python -c "import sysconfig; print(sysconfig.get_path('platstdlib'))") \
    && echo $PYTHON_LIB \
    && rm -r \
    $PYTHON_LIB/site-packages \
    # $PYTHON_LIB/lib-dynload \
    $PYTHON_LIB/ensurepip

# Remove all __pycache__ folders and their content
RUN find . -type d -name __pycache__ -exec rm -r {} \+

# Squash image with trick https://stackoverflow.com/a/56118557/10882657
FROM scratch
COPY --from=base / /
WORKDIR /root/fastapi_server
ENV PYTHONPATH=$PYTHONPATH:/root/fastapi_server/src
ENV PATH="/root/fastapi_server/.venv/bin:$PATH"
CMD ["litestar", "--app-dir", "src", "run", "--host", "0.0.0.0", "--port", "8000"]
