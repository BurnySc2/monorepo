#!/usr/bin/env bash
# WHY fail fast on broken setup playbooks before deploy.
set -euo pipefail
cd "$(dirname "$0")"
# WHY catch compose errors before ansible runs.
check_compose() {
  command -v docker >/dev/null || { echo "SKIP: docker missing"; return 0; }
  fails=0
  for f in service_*/docker-compose.yml; do
    docker compose -f "$f" config --no-interpolate || { echo "FAIL $f"; fails=$((fails+1)); }
  done
  [ "$fails" -eq 0 ] || return 1
}
# WHY reuse one play list for syntax and secrets checks.
check_syntax() {
  command -v ansible-playbook >/dev/null || { echo "SKIP: ansible missing"; return 0; }
  for play in service_*/*_setup.yml; do
    echo "==> $play"
    ansible-playbook -i hosts "$play" --syntax-check --check
  done
}
# WHY verify vault-backed runs without printing values.
check_secrets() {
  command -v ansible-playbook >/dev/null || { echo "SKIP: ansible missing"; return 0; }
  SECRETS="${ANSIBLE_SECRETS:-/home/burny/syncthing/secrets/ansible_secrets/.ansible_secrets}"
  [ -f "$SECRETS" ] || { echo "SKIP: secrets not found"; return 0; }
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
