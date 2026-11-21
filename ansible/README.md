# Ansible Services

Deploys Docker services to local and remote hosts with Ansible.
Each `service_*/` directory holds one `docker-compose.yml` template
plus one `*_setup.yml` playbook that creates the user, copies the
compose file, and starts the stack.

## 1. Inventory Map

Groups are defined in `inventory/hosts`.
Run playbooks from inside `ansible/` so `-i inventory` resolves.

| Group          | Members                         | Use when                    |
| -------------- | ------------------------------- | --------------------------- |
| my_servers     | prodesk, burnylaptopd, contabo2 | Target every host           |
| local_servers  | prodesk, burnylaptopd           | Target LAN hosts only       |
| remote_servers | contabo2                        | Target rented host only     |
| server_group1  | prodesk                         | Single local workstation    |
| server_group2  | burnylaptopd                    | Single local laptop         |
| server_group3  | contabo2                        | Remote host services        |
| server_group4  | contabo2                        | Remote host services        |
| traefik_front  | contabo2                        | Legacy edge entrypoint host |

`server_group3` points at `contabo2`. Both `server_group3` and
`server_group4` currently resolve to the same remote host; pick the
group named in the playbook you run.

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
Install the collection once per control machine:

```sh
ansible-galaxy collection install community.docker
```

Versioned pointers live in `setup_pc/` requirements files, e.g.
`setup_pc/setup_arch/requirements.yml` pins `community.general`
and `kewlfft.aur`.
Use the requirements file when bootstrapping a fresh laptop.

## 4. Deploy Example

Run one service at a time from `ansible/`. This example deploys
Filebrowser to `server_group4`:

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
  `service_stirling/docker-compose.yml`,
  `service_uptime_kuma/docker-compose.yml`.
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

YAML autoformat is `yamlfix` via `uv`, configured in `pyproject.toml [tool.yamlfix]` (line_length=200, sequence_style=block_style, none_representation="null", allow_duplicate_keys=true). `yamllint` (`.yamllint.yml`) is lint-only.

```sh
# format one file
uv run --group dev yamlfix <file.yml>
# format whole repo
uv run --group dev yamlfix .
# check-only
uv run --group dev yamlfix --check .
# lint after fixing
uv run --group dev yamllint .
```

Run `yamlfix` before `yamllint`; review `git diff` after first run (block_style/null can cause cosmetic diffs).
Diff output is always on via `[diff] always = True` in `ansible.cfg`, so `--diff` is redundant.

`ansible-lint` (`check.sh check_ansible_lint`) is check-only in CI: `uv run --group dev ansible-lint --strict site.yml provision_docker_networks.yml setup_cloudflare_a_record.yml redeploy_selected.yml service_*/*_setup.yml tasks/ setup_pc/ --exclude .venv/ --exclude service_*/templates/`. Baseline is 361 violations (var-naming 129, fqcn 71, risky-file-permissions 42, rest mixed) burned down separately, not gated to zero. Local auto-fix is `ansible-lint --fix=yaml,fqcn,key-order,jinja` only, then review `git diff`. Order is `yamlfix` first, then `yamllint`/`ansible-lint`; `.venv` and `service_*/templates/*.j2` are excluded. `check.sh` ends with `PASS: compose, syntax, secrets checks done`, which names compose/syntax/secrets only — yaml/lint gates run earlier in the same script.
