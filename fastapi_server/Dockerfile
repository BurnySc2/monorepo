FROM python:3.10-slim

ADD poetry.lock pyproject.toml /root/fastapi_server/

WORKDIR /root/fastapi_server

RUN pip install poetry --no-cache-dir \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev

ADD . /root/fastapi_server/fastapi_server

CMD ["poetry", "run", "uvicorn", "fastapi_server.main:app", "--host", "0.0.0.0", "--port", "8000"]

# See run.sh
