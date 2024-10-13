FROM python:3.12-alpine

RUN pip install --no-cache-dir poetry==1.8 \
    && yes | poetry cache clear PyPI --all

WORKDIR /root/stream_announcer

COPY poetry.lock pyproject.toml ./

RUN poetry install --without dev

COPY src /root/stream_announcer/src

ENV PYTHONPATH=$PYTHONPATH:/root/stream_announcer

CMD ["poetry", "run", "python", "src/stream_announcer.py"]
