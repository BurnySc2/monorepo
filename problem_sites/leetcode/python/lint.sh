#!/usr/bin/env bash
# WHY gate python drift with ruff/pyrefly before push: see .github/workflows/leetcode_python.yml
set -euo pipefail
cd "$(dirname "$0")"
command -v uv >/dev/null || { if [[ ${LINT_STRICT:-0} == 1 ]]; then echo "FAIL: uv missing (strict)"; exit 1; fi; echo "SKIP: uv missing"; exit 0; }
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
