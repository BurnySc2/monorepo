#!/bin/sh
# Run once after `docker compose up` — idempotent, safe to run multiple times
NODE_ID=$(docker exec fastapi_dev_garage /garage node id | cut -d@ -f1)
docker exec fastapi_dev_garage /garage layout assign -z local -c 1G "$NODE_ID"
CURRENT=$(docker exec fastapi_dev_garage /garage layout show 2>&1 | grep 'Current cluster layout version:' | grep -oP '\d+$')
NEXT_VERSION=$((CURRENT + 1))
docker exec fastapi_dev_garage /garage layout apply --version "$NEXT_VERSION"

# Create key
docker exec fastapi_dev_garage /garage key create fastapi
docker exec fastapi_dev_garage /garage key list
# docker exec fastapi_dev_garage /garage key delete --yes <keyname>
# Allow create bucket
docker exec fastapi_dev_garage /garage key allow --create-bucket fastapi

# Create bucket
docker exec fastapi_dev_garage /garage bucket create garage-audiobook-bucket
# Assign key to bucket
docker exec fastapi_dev_garage /garage bucket allow --read --write --owner garage-audiobook-bucket --key fastapi
docker exec fastapi_dev_garage /garage bucket info garage-audiobook-bucket
# Set bucket quota
docker exec fastapi_dev_garage /garage bucket set-quotas --max-size 10GB garage-audiobook-bucket
