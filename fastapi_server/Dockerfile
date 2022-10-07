FROM python:3.10-slim

RUN apt install ffmpeg -y

ADD poetry.lock pyproject.toml /root/fastapi_server/

WORKDIR /root/fastapi_server

RUN pip install poetry --no-cache-dir \
    && poetry install --no-dev

ADD . /root/fastapi_server

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# See run.sh
