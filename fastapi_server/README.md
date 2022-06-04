# Fastapi sqlmodel webserver

## Launch local dev server

```
poetry run uvicorn fastapi_server.main:app --host localhost --port 8000 --reload
```
Now you can go to `http://0.0.0.0:8000` or `http://0.0.0.0:8000/docs` to check out the documentation to all endpoints

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
