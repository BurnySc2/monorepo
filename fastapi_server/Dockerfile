FROM python:3.12-slim

# Install ffmpeg
# RUN export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -qq update \
#     && apt-get -qq install --no-install-recommends \
#     ffmpeg \
#     && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.8 \
    && yes | poetry cache clear PyPI --all

WORKDIR /root/fastapi_server

COPY poetry.lock pyproject.toml ./

RUN poetry install --without dev

COPY . /root/fastapi_server

ENV PYTHONPATH "${PYTHONPATH}:/root/fastapi_server"

CMD ["poetry", "run", "litestar", "run", "--host", "0.0.0.0", "--port", "8000"]
