FROM python:3.10-slim

ENV POETRY_VENV=/app/.venv

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -qq update \
    && apt-get -qq install --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.4.0

COPY pyproject.toml poetry.lock /app/

WORKDIR /app

RUN poetry install 

COPY app /app/

ENTRYPOINT [ "sleep", "1" ]
