FROM python:3.10-slim

# Install ffmpeg
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -qq update \
    && apt-get -qq install --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.5.1

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev

COPY src/ /app/src/

# Allow imports to function correctly
ENV PYTHONPATH=/app

ENTRYPOINT [ "poetry", "run", "python", "src/worker.py" ]
