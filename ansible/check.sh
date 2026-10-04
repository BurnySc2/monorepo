#!/usr/bin/env bash
# WHY fail fast on broken setup playbooks before deploy.
set -euo pipefail
cd "$(dirname "$0")"
# WHY fail strict gates when tools missing in CI.
strict_skip() {
  if [[ ${LINT_STRICT:-0} == 1 ]]; then echo "FAIL: $1 missing (strict)"; return 1; fi
  echo "SKIP: $1 missing"
  return 0
}
# WHY catch compose errors before ansible runs.
check_compose() {
  command -v docker >/dev/null || { strict_skip "docker"; return $?; }
  local fails=0
  for f in service_*/docker-compose.yml; do
    docker compose -f "$f" config --no-interpolate || { echo "FAIL $f"; fails=$((fails+1)); }
  done
  [ "$fails" -eq 0 ] || return 1
}
# WHY reuse one play list for syntax and secrets checks.
check_syntax() {
  command -v ansible-playbook >/dev/null || { strict_skip "ansible"; return $?; }
  for play in service_*/*_setup.yml; do
    echo "==> $play"
    ansible-playbook -i hosts "$play" --syntax-check --check
  done
}
# WHY verify vault-backed runs without printing values.
# WHY always SKIP when secrets file missing even in strict: vault not in CI, syntax already gated by check_syntax; set ANSIBLE_SECRETS to enable.
check_secrets() {
  command -v ansible-playbook >/dev/null || { strict_skip "ansible"; return $?; }
  SECRETS="${ANSIBLE_SECRETS:-/home/burny/syncthing/secrets/ansible_secrets/.ansible_secrets}"
  if [ ! -f "$SECRETS" ]; then
    echo "SKIP: secrets not found (vault not in CI; set ANSIBLE_SECRETS to enable)"
    return 0
  fi
  for play in service_*/*_setup.yml; do
    echo "==> $play + secrets"
    ansible-playbook -i hosts -i "$SECRETS" "$play" --syntax-check --check --diff
  done
}
main() {
  check_compose
  check_syntax
  check_secrets
  echo "PASS: compose, syntax, secrets checks done"
}
main "$@"
