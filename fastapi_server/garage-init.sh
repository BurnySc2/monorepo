#!/bin/sh
# Run once after `docker compose up` — idempotent, safe to run multiple times
NODE_ID=$(docker exec fastapi_dev_garage /garage node id | cut -d@ -f1)
docker exec fastapi_dev_garage /garage layout assign -z local -c 1G "$NODE_ID"
CURRENT=$(docker exec fastapi_dev_garage /garage layout show 2>&1 | grep 'Current cluster layout version:' | grep -oP '\d+$')
NEXT_VERSION=$((CURRENT + 1))
docker exec fastapi_dev_garage /garage layout apply --version "$NEXT_VERSION"
