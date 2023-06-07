FROM python:3.10-slim

RUN pip install poetry==1.5.1

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev

COPY src/ /app/src/

ENTRYPOINT [ "poetry", "run", "python", "src/worker.py" ]
