# Ansible Services

Deploys Docker services to local and remote hosts with Ansible.
Each `service_*/` directory holds one `docker-compose.yml` template
plus one `*_setup.yml` playbook that creates the user, copies the
compose file, and starts the stack.

## 1. Inventory Map

Groups are defined in `hosts` at the `ansible/` root.
Run playbooks from inside `ansible/` so `-i ../hosts` resolves.

| Group | Members | Use when |
| --- | --- | --- |
| my_servers | prodesk, burnylaptopd, contabo2 | Target every host |
| local_servers | prodesk, burnylaptopd | Target LAN hosts only |
| remote_servers | contabo2 | Target rented host only |
| server_group1 | prodesk | Single local workstation |
| server_group2 | burnylaptopd | Single local laptop |
| server_group3 | contabo2 | Remote host services |
| server_group4 | contabo2 | Remote host services |
| traefik_front | contabo2 | Legacy edge entrypoint host |

`server_group3` points at `contabo2`. Both `server_group3` and
`server_group4` currently resolve to the same remote host; pick the
group named in the playbook you run.

## 2. Secrets Bootstrap

Secrets live outside this repo and are never committed.
Playbooks read them through a second inventory entry:

```sh
export ANSIBLE_SECRETS=/home/burny/syncthing/secrets/ansible_secrets/.ansible_secrets
ansible-playbook service_filebrowser/filebrowser_setup.yml -i ../hosts -i $ANSIBLE_SECRETS
```

The pattern is always `-i ../hosts -i $ANSIBLE_SECRETS`.
Templates reference values as `{{ secrets.MY_PUBLIC_DOMAIN }}` and similar
placeholders; no real values belong in this repo.

## 3. Galaxy Install

Playbooks use `community.docker.docker_compose_v2` to manage stacks.
Install the collection once per control machine:

```sh
ansible-galaxy collection install community.docker
```

Versioned pointers live in `setup_pc/` requirements files, e.g.
`setup_pc/setup_chromebook/requirements.yml` pins `community.docker`
alongside `community.general` and `kewlfft.aur`.
Use the requirements file when bootstrapping a fresh laptop.

## 4. Deploy Example

Run one service at a time from `ansible/`. This example deploys
Filebrowser to `server_group4`:

```sh
ansible-playbook service_filebrowser/filebrowser_setup.yml -i ../hosts -i $ANSIBLE_SECRETS
```

The playbook creates the service user, writes
`/home/<service>/docker-compose.yml` on the target, then runs
compose down and up. There are 41 absolute `/home/burny/syncthing`
references left across playbook headers; converting them to the
`$ANSIBLE_SECRETS` pattern is recorded but left for a later change.

## 5. Ingress Decision

Pangolin is the entrypoint for public traffic.
See `service_traefik/DEPRECATED.md` for the frozen legacy stack.

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

| Image | Pin | Policy |
| --- | --- | --- |
| mariadb | 10.11 | Long-term release line in Bookstack |
| redis | 7-alpine, 8-alpine | Major-pinned per service (Paperless and Reactive Resume on 7, Docmost on 8) |
| postgres | 15-alpine, 16-alpine | 16 is the fleet standard; Reactive Resume stays on 15 for app support |
| pihole | rolling release | Tracks upstream, pin to dated release later |
| pangolin, gerbil | rolling release | Tracks upstream, pin to dated release later |
| traefik | 3.3.4 frozen, v3.6 active | 3.3.4 stays frozen in legacy stack; v3.6 serves the Pangolin stack |
| wireguard | rolling release | Intentional rolling tag in legacy traefik compose files |
| compose pull | missing | 7 setup playbooks use `pull: missing` (docmost, paperless, pangolin, pihole, bookstack, reactive_resume, postgres) |
