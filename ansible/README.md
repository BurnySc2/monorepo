# Ansible Services

Deploys Docker services to local and remote hosts with Ansible.
Each `service_*/` directory holds one `docker-compose.yml` template
plus one `*_setup.yml` playbook that creates the user, copies the
compose file, and starts the stack.

## 1. Inventory Map

Groups are defined in `inventory/hosts`.
Run playbooks from inside `ansible/` so `-i inventory` resolves.

| Group          | Members                         | Use when                |
| -------------- | ------------------------------- | ----------------------- |
| my_servers     | prodesk, burnylaptopd, contabo2 | Target every host       |
| local_servers  | prodesk, burnylaptopd           | Target LAN hosts only   |
| remote_servers | contabo2                        | Target rented host only |

## 2. Secrets Bootstrap

Secrets live outside this repo and are never committed.
Playbooks read them through a second inventory entry:

```sh
export ANSIBLE_SECRETS=/home/burny/syncthing/secrets/ansible_secrets/.ansible_secrets
ansible-playbook service_filebrowser/filebrowser_setup.yml -i inventory -i $ANSIBLE_SECRETS
```

The pattern is always `-i inventory -i $ANSIBLE_SECRETS`.
Templates reference values as `{{ secrets.MY_PUBLIC_DOMAIN }}` and similar
placeholders; no real values belong in this repo.

## 3. Galaxy Install

Playbooks use `community.docker.docker_compose_v2` to manage stacks.
The top-level `requirements.yml` is the CI superset — it pins
`community.docker`, `community.general`, `ansible.posix`, and
`kewlfft.aur`. `check.sh` installs it first via
`ansible-galaxy collection install -r requirements.yml`, so
fully-qualified names resolve before lint/syntax run.

Nested files (e.g. `setup_pc/setup_arch/requirements.yml`) remain
for standalone `run.sh` bootstraps of a fresh laptop.
Set `ANSIBLE_GALAXY_SKIP=1` to skip the galaxy install on offline runs.

## 4. Deploy Example

Run one service at a time from `ansible/`. This example deploys
Filebrowser to `contabo2`:

```sh
ansible-playbook service_filebrowser/filebrowser_setup.yml -i inventory -i $ANSIBLE_SECRETS
```

The playbook creates the service user, writes
`/home/<service>/docker-compose.yml` on the target, then runs
compose down and up. For `redeploy_selected.yml`, `--tags apps` redeploys
the 18 web services, `--tags games` redeploys only the 4 game servers
on prodesk (satisfactory, v_rising, space_engineers, astroneer),
`--tags <service>` redeploys one, and `--tags apps,games` redeploys
all 22. Cleanup stays opt-in via `--tags cleanup`. There are 41 absolute `/home/burny/syncthing`
references left across playbook headers; converting them to the
`$ANSIBLE_SECRETS` pattern is recorded but left for a later change.

## 5. Ingress Decision

Pangolin is the entrypoint for public traffic (legacy traefik stack removed).

- `gerbil` in `service_pangolin/docker-compose.yml` binds `80:80`
  and `443:443`; no other stack binds those ports.
- The legacy traefik compose files keep those bindings commented
  out with an ownership note.
- New services expose only `pangolin.public-resources.*` labels.
  Reference contracts: `service_filebrowser/docker-compose.yml`,
  `service_docmost/docker-compose.yml`,
  `service_comfyui/docker-compose.yml`,
  `service_stirling/docker-compose.yml`.
- Edge routing source is `service_pangolin/traefik_config.yml`
  with `traefik_dynamic.yml` and `config.yml`.

Do not add `traefik.enable=true` or `traefik.http.*` labels to new
services.

## 6. Pinning Policy

| Image            | Pin                       | Policy                                                                                 |
| ---------------- | ------------------------- | -------------------------------------------------------------------------------------- |
| mariadb          | 10.11                     | Long-term release line in Bookstack                                                    |
| redis            | 7-alpine, 8-alpine        | Major-pinned per service (Docmost on 8)                                                |
| postgres         | 15-alpine, 16-alpine      | 16 is fleet standard                                                                   |
| pihole           | rolling release           | Tracks upstream, pin to dated release later                                            |
| pangolin, gerbil | rolling release           | Tracks upstream, pin to dated release later                                            |
| traefik          | 3.3.4 frozen, v3.6 active | 3.3.4 stays frozen in legacy stack; v3.6 serves the Pangolin stack                     |
| wireguard        | rolling release           | Intentional rolling tag in legacy traefik compose files                                |
| compose pull     | missing                   | 5 setup playbooks use `pull: missing` (docmost, pangolin, pihole, bookstack, postgres) |

## 7. Formatting

`yamllint` (`.yamllint.yml`) is the sole YAML gate.
Check with:

```sh
uv run --group dev yamllint .
```

Diff output is always on via `[diff] always = True` in `ansible.cfg`, so `--diff` is redundant.

`ansible-lint` (`.ansible-lint`, `check.sh check_ansible_lint`) is check-only in CI: `uv run --group dev ansible-lint --strict setup_cloudflare_a_record.yml redeploy_selected.yml service_*/*_setup.yml backup/backup_setup.yml tasks/ setup_pc/ --exclude .venv/ --exclude service_*/templates/ --exclude backup/templates/`. Four style-debt rules (`var-naming`, `role-name`, `no-role-prefix`, `no-relative-paths`) moved from `warn_list` to `skip_list` with a ticket link (`yaml` stays skipped, `profile: moderate`); `--strict` is kept so remaining violations still fail. Local auto-fix is `ansible-lint --fix=yaml,fqcn,key-order,jinja` only, then review `git diff`. `.venv` and `service_*/templates/*.j2` are excluded. `check.sh` runs galaxy -> yaml -> lint -> compose -> syntax -> secrets and ends with `PASS: compose, syntax, secrets checks done`, which names compose/syntax/secrets only — galaxy/yaml/lint gates run earlier in the same script.
