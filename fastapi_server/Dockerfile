FROM python:3.11-slim

# Install ffmpeg
RUN apt -y update && \
    apt install -y --no-install-recommends ffmpeg

ADD poetry.lock pyproject.toml /root/fastapi_server/

WORKDIR /root/fastapi_server

RUN pip install poetry --no-cache-dir \
    && poetry install --no-dev

ADD . /root/fastapi_server

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# See run.sh
