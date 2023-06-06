FROM python:3.10-slim

# TODO Check if ffmpeg is even necessay
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -qq update \
    && apt-get -qq install --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# RUN pip install poetry
RUN pip install poetry==1.4.0

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install

COPY src /app/src
COPY SECRETS.toml /app/

ENTRYPOINT [ "sleep", "1" ]
