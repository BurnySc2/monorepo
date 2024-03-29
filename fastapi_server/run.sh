set -e
docker build -t burnysc2/fastapi_server:latest .
docker run --rm --name fastapi_server --env STAGE=DEV \
  -p 8000:8000 \
  --mount type=bind,source="$(pwd)/data",destination=/root/data \
  burnysc2/fastapi_server:latest
