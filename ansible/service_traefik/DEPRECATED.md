# DEPRECATED — pangolin bundle is SSOT for edge routing

This stack (`service_traefik/`) is frozen. Do not extend it.

## WHY deprecated

- Pangolin bundle owns `80/443` (traefik v3.6 via `service_pangolin/traefik_config.yml`).
- Legacy traefik `3.3.4` here is pinned and must not be upgraded.
- Gerbil/pangolin handles public entrypoints; this stack only remains for local history.

## What still reads it

- `dynamic.yml` — frozen file-provider routers/services (no new entries).
- `traefik.yml` — frozen static config (entryPoints, cert resolvers, providers).
- `docker-compose.yml` / `docker-compose_remote.yml` — kept hardened, dashboard disabled.

## What NOT to do

- No new routers in `dynamic.yml`.
- No `traefik.enable=true` labels on services (use `pangolin.public-resources.*` labels).
- No new `traefik.http.*` labels, middlewares, or cert resolvers.
- Do not re-enable `--api.insecure=true` or `80:80` / `443:443` bindings.

## Migration pointer

- Per-service cutover: comfyui/stirling/uptime-kuma pattern.
- Reference contract: `service_filebrowser/docker-compose.yml`, `service_docmost/docker-compose.yml`.
- Edge SSOT: `service_pangolin/traefik_config.yml` (+ `traefik_dynamic.yml`, `config.yml`).

## Rollback note

- Rollback is file restore only: `git log -- ansible/service_traefik/` then restore prior compose/config.
- Do not run old and new edge stacks bound to `80/443` at the same time.
- Verify with `docker ps` (no `traefik:3.3.4` listening) and pangolin dashboard resources.
