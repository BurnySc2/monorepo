FROM python:3.12-alpine

RUN pip install --no-cache-dir poetry==1.8 \
    && yes | poetry cache clear PyPI --all

WORKDIR /announcer

COPY poetry.lock pyproject.toml ./

RUN poetry install --without dev

COPY src /announcer/src

CMD ["poetry", "run", "python", "src/main.py"]
