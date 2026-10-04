#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# WHY inherit LINT_STRICT from env so strict gates apply in check.sh.
exec ./check.sh "$@"
