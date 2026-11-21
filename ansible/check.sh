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
# WHY gate YAML format before compose/syntax checks.
check_yaml_format() {
  command -v uv >/dev/null || { strict_skip "uv"; return $?; }
  uv run --group dev yamlfix --check --exclude '.venv/**/*' .
  uv run --group dev yamllint --strict .
}
# WHY lint playbooks before compose/syntax checks.
check_ansible_lint() {
  command -v uv >/dev/null || { strict_skip "uv"; return $?; }
  uv run --group dev ansible-lint --strict setup_cloudflare_a_record.yml redeploy_selected.yml service_*/*_setup.yml tasks/ setup_pc/ --exclude .venv/ --exclude service_*/templates/
}
# WHY catch compose errors before ansible runs.
check_compose() {
  command -v docker >/dev/null || { strict_skip "docker"; return $?; }
  local fails=0
  for f in service_*/docker-compose.yml service_*/templates/docker-compose.yml.j2; do
    [ -e "$f" ] || continue
    if [[ "$f" == *.j2 ]]; then
      echo "==> $f (template - skip engine config, covered by render-then-lint)"
      continue
    else
      docker compose -f "$f" config --no-interpolate || { echo "FAIL $f"; fails=$((fails+1)); }
    fi
  done
  [ "$fails" -eq 0 ] || return 1
}
# WHY cover both jinja branches of syncthing template render.
check_render_lint() {
  command -v docker >/dev/null || { strict_skip "docker"; return $?; }
  command -v ansible >/dev/null || { strict_skip "ansible"; return $?; }
  command -v uv >/dev/null || { strict_skip "uv"; return $?; }
  local tmp
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' RETURN
  ansible localhost -c local -i localhost, -m ansible.builtin.template -a "src=service_syncthing/templates/docker-compose.yml.j2 dest=$tmp/member.yml" -e '{"group_names":["server_group1"],"USER_ID":{"stdout":"1000"},"GROUP_ID":{"stdout":"1000"},"inventory_hostname":"dummy","SYNCTHING_URL":"https://example.com","APPLICATION_PORT":"8384"}' >/dev/null
  ansible localhost -c local -i localhost, -m ansible.builtin.template -a "src=service_syncthing/templates/docker-compose.yml.j2 dest=$tmp/plain.yml" -e '{"group_names":[],"USER_ID":{"stdout":"1000"},"GROUP_ID":{"stdout":"1000"},"inventory_hostname":"dummy","SYNCTHING_URL":"https://example.com","APPLICATION_PORT":"8384"}' >/dev/null
  uv run --group dev yamllint --strict "$tmp/member.yml" "$tmp/plain.yml"
  docker compose -f "$tmp/member.yml" config --no-interpolate >/dev/null
  docker compose -f "$tmp/plain.yml" config --no-interpolate >/dev/null
  grep -q /media/ssd480 "$tmp/member.yml" || { echo "FAIL member render missing /media/ssd480"; return 1; }
  grep -q /media/ssd480 "$tmp/plain.yml" && { echo "FAIL plain render leaks /media/ssd480"; return 1; } || true
}
# WHY reuse one play list for syntax and secrets checks.
check_syntax() {
  command -v ansible-playbook >/dev/null || { strict_skip "ansible"; return $?; }
  for play in service_*/*_setup.yml; do
    echo "==> $play"
    ansible-playbook -i inventory "$play" --syntax-check --check
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
    ansible-playbook -i inventory -i "$SECRETS" "$play" --syntax-check --check
  done
}
main() {
  check_yaml_format
  check_ansible_lint
  check_compose
  check_render_lint
  check_syntax
  check_secrets
  echo "PASS: compose, syntax, secrets checks done"
}
main "$@"
