FROM python:3.10-slim

ADD poetry.lock pyproject.toml /root/fastapi_server/

WORKDIR /root/fastapi_server

RUN pip install poetry --no-cache-dir \
    && poetry install --no-dev

ADD . /root/fastapi_server/fastapi_server

WORKDIR /root/fastapi_server

CMD ["poetry", "run", "uvicorn", "fastapi_server.main:app", "--host", "0.0.0.0", "--port", "8000"]

# docker build -t fastapi_server .
# docker run -d --rm --name fastapitest -p 8000:8000 --mount type=bind,source="$(pwd)/data",destination=/root/fastapi_server/data fastapi_server
