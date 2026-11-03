#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
ROOT="$(dirname "$APP_DIR")"
if [[ -f "$APP_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1090,SC1091
  source "$APP_DIR/.env"
  set +a
fi
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1090,SC1091
  source "$ROOT/.env"
  set +a
fi
if [[ -z "${DATABASE_URL:-}" && -z "${PGHOST:-}" ]]; then
  echo "error: DATABASE_URL or PGHOST must be set (via twitch_announcer_gleam/.env or root .env)" >&2
  exit 1
fi
if command -v pg_isready >/dev/null 2>&1; then
  pg_isready || echo "warning: database not ready, continuing anyway" >&2
else
  echo "warning: pg_isready not found, skipping readiness check" >&2
fi
cd "$APP_DIR"
gleam run -m squirrel
gleam run -m squirrel check
