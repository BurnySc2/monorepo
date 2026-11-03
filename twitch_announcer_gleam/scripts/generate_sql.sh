#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
DB_URL=${POSTGRES_CONNECTION_STRING:-${DATABASE_URL:?missing}}
pg_isready || echo "warning: database not ready, continuing anyway" >&2
psql "$DB_URL" -v ON_ERROR_STOP=1 -f test/fixtures/c3_fixture.sql
gleam run -m squirrel
gleam run -m squirrel check
