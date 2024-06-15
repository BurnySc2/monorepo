# Fastapi sqlmodel webserver

## Requirements

Python >=3.8.1 <3.13
Local postgres db via

```sh
docker run --rm --name postgres \
    -e POSTGRES_USER=postgres\
    -e POSTGRES_PASSWORD=123 \
    -p 5432:5432 \
    -v postgres_data:/var/lib/postgresql/data \
    postgres:15-alpine
```

## Launch local dev server

```
POSTGRES_CONNECTION_STRING="postgresql://postgres:123@localhost:5432/postgres" poetry run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Now you can go to `https://0.0.0.0:8000` or `https://0.0.0.0:8000/docs` to check out the documentation to all endpoints

During development, the backend server is used to serve the frontend.

## Deploy

- Requiement: docker

On the server, either build the docker image via

```
docker build -t burnysc2/fastapi_server:latest .
```

or pull the latest image

```
docker pull burnysc2/fastapi_server:latest
```

now run it with a `data` subfolder mounted which will be persistent

```
docker run --rm --name fastapitest --publish 8000:8000 --env STAGE=PROD --mount type=bind,source="$(pwd)/data",destination=/root/fastapi_server/data burnysc2/fastapi_server:latest
```

# Create postgres user and permissions to create tables

```sql
-- Create user
CREATE USER litestar_server_dev WITH PASSWORD 'your_password';
GRANT CREATE ON SCHEMA public TO litestar_server_dev;
```

# Ideal structure of the project
```mermaid
---
title: "Stages: dev, staging, prod, test"
---
mindmap
  root((mindmap))
    www.my_domain.com Stage: PROD, most stable release
    staging.my_domain.com Stage: STAGING, experimental release
    localhost, Stage: DEV, under development, uses local sqlite database
    no domain, Stage: Test, under development, uses local sqlite or memory database
```
