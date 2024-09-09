FROM python:3.12-alpine

# Install ffmpeg
RUN apk update \
    && apk upgrade \
    && apk add --no-cache ffmpeg npm

# Install poetry
RUN pip install --no-cache-dir poetry==1.8

WORKDIR /root/fastapi_server

COPY poetry.lock pyproject.toml ./

RUN poetry install --without dev

# Prepare prisma client and generate types
COPY prisma/schema.prisma /root/fastapi_server/prisma/schema.prisma
RUN poetry run prisma generate

COPY . /root/fastapi_server

ENV PYTHONPATH "${PYTHONPATH}:/root/fastapi_server"

CMD ["poetry", "run", "litestar", "run", "--host", "0.0.0.0", "--port", "8000"]
