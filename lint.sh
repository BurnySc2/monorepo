#!/usr/bin/env bash
# WHY fail fast on yaml/workflow/docker drift before push.
set -euo pipefail
cd "$(dirname "$0")"
# WHY fail strict gates when tools missing in CI.
strict_skip() {
  if [[ ${LINT_STRICT:-0} == 1 ]]; then echo "FAIL: $1 missing (strict)"; return 1; fi
  echo "SKIP: $1 missing"
  return 0
}
# WHY catch yaml style drift before CI runs.
check_yamllint() {
  command -v yamllint >/dev/null || { strict_skip "yamllint"; return $?; }
  yamllint .github/workflows/
}
# WHY catch invalid workflow yaml before lint runs.
check_yaml_parse() {
  command -v python3 >/dev/null || { strict_skip "python3" || return 1; return 0; }
  python3 -c "import yaml" >/dev/null 2>&1 || { strict_skip "python yaml (pyyaml)" || return 1; return 0; }
  python3 - <<'PY'
import pathlib
import yaml
for f in sorted(pathlib.Path(".github/workflows").glob("*.yml")):
    yaml.safe_load(f.read_text())
print("PASS: yaml parse")
PY
}
# WHY catch stale checkout pins.
check_workflow_greps() {
  if grep -rn 'checkout@v[0-5]' .github/workflows/; then
    echo "FAIL: stale checkout pin found"
    return 1
  fi
  echo "PASS: workflow greps"
}
# WHY catch trailing whitespace in non-Python files without extra binary.
check_whitespace() {
  if grep -rnE '[[:blank:]]+$' --include='*.yml' --include='*.yaml' --include='*.md' --include='*.sql' --include='*.toml' --include='*.sh' --include='Dockerfile*' --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.ruff_cache .github/ fastapi_server/ discord_bot/ transcribe_website/transcriber_backend/ python_examples/ problem_sites/leetcode/python/ burny_common/ twitch_stream_announcer/ ansible/; then
    echo "FAIL: trailing whitespace found"
    return 1
  fi
  echo "PASS: whitespace"
}
# WHY catch Dockerfile syntax errors before registry push.
# WHY mirror docker_build.yml matrix so local and CI build same images.
check_docker_syntax() {
  command -v docker >/dev/null || { strict_skip "docker" || return 1; return 0; }
  local fails=0
  for d in fastapi_server discord_bot twitch_stream_announcer transcribe_website/transcriber_backend; do
    echo "==> $d"
    if docker build --help 2>&1 | grep -q -- '--check'; then
      docker build --check -f "$d/Dockerfile" "$d" || { echo "FAIL $d"; fails=$((fails+1)); }
    else
      # WHY old docker without --check cannot validate syntax; fail strict gates.
      if [[ ${LINT_STRICT:-0} == 1 ]]; then echo "FAIL: docker build --check unsupported for $d (strict)"; fails=$((fails+1)); else echo "SKIP: docker build --check unsupported for $d"; fi
    fi
  done
  [ "$fails" -eq 0 ] || return 1
}
# WHY surface optional linters without blocking local runs.
# WHY fail strict gates on findings so CI blocks drift.
check_optional() {
  if command -v hadolint >/dev/null; then
    hadolint fastapi_server/Dockerfile discord_bot/Dockerfile twitch_stream_announcer/Dockerfile transcribe_website/transcriber_backend/Dockerfile || {
      if [[ ${LINT_STRICT:-0} == 1 ]]; then echo "FAIL: hadolint findings (strict)"; return 1; fi
    }
  else
    echo "SKIP: hadolint missing"
  fi
  if command -v actionlint >/dev/null; then
    actionlint || {
      if [[ ${LINT_STRICT:-0} == 1 ]]; then echo "FAIL: actionlint findings (strict)"; return 1; fi
    }
  else
    echo "SKIP: actionlint missing"
  fi
}
# WHY reuse per-project lint scripts so CI matches local runs.
check_projects() {
  local fails=0
  for d in fastapi_server discord_bot transcribe_website/transcriber_backend python_examples problem_sites/leetcode/python burny_common twitch_stream_announcer ansible; do
    echo "==> $d"
    if [ ! -x "$d/lint.sh" ]; then strict_skip "$d/lint.sh" || fails=$((fails+1)); continue; fi
    "$d/lint.sh" || { echo "FAIL $d"; fails=$((fails+1)); }
  done
  # WHY skip svelte_frontends: npm lint/check run in svelte_frontends.yml excluded from grep scope.
  [ "$fails" -eq 0 ] || return 1
}
main() {
  check_yamllint
  check_yaml_parse
  check_workflow_greps
  check_whitespace
  check_docker_syntax
  check_projects
  check_optional
  echo "PASS: yamllint, yaml parse, greps, whitespace, docker checks done"
}
main "$@"
