#!/usr/bin/env bash
set -euo pipefail
source .env
cd src
DATABASE_URL=$POSTGRES_CONNECTION_STRING gleam run -m squirrel
DATABASE_URL=$POSTGRES_CONNECTION_STRING gleam run -m squirrel check
