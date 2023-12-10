FROM python:3.11-slim

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -qq update \
    && apt-get -qq install --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.5.1 \
    && yes | poetry cache clear PyPI --all

WORKDIR /root/announcer

COPY poetry.lock pyproject.toml ./

RUN poetry install --without dev

COPY src /root/announcer/src

CMD ["poetry", "run", "python", "src/main.py"]
