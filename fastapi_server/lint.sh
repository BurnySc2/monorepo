#!/usr/bin/env bash
# WHY block SQL drift with ruff/pyrefly/sqlfluff before push.
set -euo pipefail
cd "$(dirname "$0")"
command -v uv >/dev/null || { if [[ ${LINT_STRICT:-0} == 1 ]]; then echo "FAIL: uv missing (strict)"; exit 1; fi; echo "SKIP: uv missing"; exit 0; }
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
uv run sqlfluff lint src/queries/
