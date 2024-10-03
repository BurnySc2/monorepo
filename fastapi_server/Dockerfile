FROM python:3.12-alpine AS base

# Install npm for prisma
RUN apk update \
    && apk upgrade \
    && apk add --no-cache npm

# Install poetry
RUN pip install --no-cache-dir poetry==1.8

COPY poetry.lock pyproject.toml /root/fastapi_server/

WORKDIR /root/fastapi_server
RUN poetry install --no-cache --without dev

# Prepare prisma client and generate types
COPY prisma/schema.prisma /root/fastapi_server/prisma/schema.prisma
RUN poetry run prisma generate

COPY . /root/fastapi_server

RUN rm -r \
    /usr/bin/node \
    /usr/lib/node_modules \
    /root/.npm \
    /root/.cache/prisma \
    # Required for interaction with prisma: /root/.cache/prisma-python \
    /root/.cache/pypoetry/artifacts \
    /root/.cache/pypoetry/cache \
    /root/.local \
    /var/cache

# Squash image with trick https://stackoverflow.com/a/56118557/10882657
FROM scratch
COPY --from=base / /
WORKDIR /root/fastapi_server
ENV PYTHONPATH=$PYTHONPATH:/root/fastapi_server
CMD ["poetry", "run", "litestar", "run", "--host", "0.0.0.0", "--port", "8000"]
