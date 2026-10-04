#!/usr/bin/env bash
# WHY block nim type/build drift before push.
set -euo pipefail
cd "$(dirname "$0")"
command -v nim >/dev/null || { if [[ ${LINT_STRICT:-0} == 1 ]]; then echo "FAIL: nim missing (strict)"; exit 1; fi; echo "SKIP: nim missing"; exit 0; }
command -v nimble >/dev/null || { if [[ ${LINT_STRICT:-0} == 1 ]]; then echo "FAIL: nimble missing (strict)"; exit 1; fi; echo "SKIP: nimble missing"; exit 0; }
nim check --hints:off src/main.nim
nimble c -d:ssl -d:release --opt:size -o:main src/main.nim
