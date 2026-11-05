# Twitch Announcer Gleam - Agent Reference

Compact reference for LLM agents. Scannable in <2 minutes.

> Single-source note: `src/main.gleam` (stages, loop, table-driven
> `update_entries`, `utc_now` `Timestamp`), `src/decide.gleam` (pure
> announce logic, `birl` + `humanize`), `src/db.gleam` (`pog` pool +
> squirrel queries, `timestamp_to_string` via `birl`, `COALESCE` reads,
> parameterized `ANY`), `src/discord.gleam` (webhooks via `kitazith`,
> `prod_stage` const), `src/twitch.gleam` (`sized_chunk` batches, shared
> send) + `src/http_helpers.gleam` (`send`, `post_json`),
> `src/dotenv.gleam` + `dot_env` (`.env` loading), `scripts/generate_sql.sh`
> (local regen), `gleam.toml` (`pog`, `gleam_time`, `gleam_otp`; no `pgo`,
> no logging lib), and `.github/workflows/twitch_announcer_gleam.yml`
> (CI) are authoritative; this file summarizes only.

---

## 1. Project Overview

Gleam (Erlang target) Twitch stream announcer:

- Polls Twitch API for enabled streams, posts Discord webhooks for newly-live
  ones, updates status in Postgres.
- `src/main.gleam`: stage dispatch — `BUILD` skips (no DB/API), `DEV` runs
  once, `PROD` loops forever with 20 s sleep; no per-stage timing logs
  (plain `io.println` only). DB connects for `DEV`/`PROD`.
- `src/main.gleam`: `update_entries` is table-driven (announced / online /
  now-offline triples via `list.try_each`, stamped with `utc_now`
  `Timestamp`); writes are `PROD`-only (`write_if_present`).
- `src/decide.gleam`: pure decision function
  `decide(rows, infos, now_epoch, grace_s)` → announced/online/offline/to-announce,
  honoring the offline grace window.
- `src/db.gleam`: `pog` pool (`pog.url_config` + actor), squirrel-generated
  `sql` queries; `timestamp_to_string` formats via `birl`, mapping the
  `1970-01-01` epoch to `""` (unknown time).
- `src/twitch.gleam`: token + stream infos, names lowercased, 20 per
  Helix request (`chunks` wraps `list.sized_chunk`), offline defaults for
  missing; all HTTP via `http_helpers.send`.
- `src/discord.gleam`: `kitazith` embeds + validation; real POSTs via
  `http_helpers.post_json` only in `PROD` (`prod_stage` const), payload
  only logged otherwise.

Stack: Gleam 1.19.2 on OTP 27 + PostgreSQL (`pog` driver).

---

## 2. Quick Reference

| Command                         | Description                                           |
| ------------------------------- | ----------------------------------------------------- |
| `gleam deps download`           | Fetch dependencies (cwd is `twitch_announcer_gleam/`) |
| `gleam build`                   | Compile                                               |
| `gleam check`                   | Type-check                                            |
| `gleam format --check src test` | Format check (CI-enforced)                            |
| `gleam test`                    | Run `gleeunit` tests in `test/`                       |
| `gleam run`                     | Run once (`DEV`) or forever (`PROD`) per `STAGE`      |
| `./scripts/generate_sql.sh`     | Local squirrel regen (needs live DB; never in CI)     |

| Path                      | Purpose                                                           |
| ------------------------- | ----------------------------------------------------------------- |
| `src/main.gleam`          | Entry `main`, `STAGE` dispatch, `run_once`, `loop_forever` (20 s) |
| `src/decide.gleam`        | Pure announce-decision logic + time parsing/formatting            |
| `src/db.gleam`            | `pog` pool, squirrel queries, row mapping to `DbRow`              |
| `src/sql.gleam`           | Generated bindings (never hand-edit)                              |
| `src/sql/`                | Query sources (`COALESCE` read; `ANY($1/$2)` writes)              |
| `src/twitch.gleam`        | Twitch token + stream-info fetching                               |
| `src/discord.gleam`       | Discord webhook posting (`kitazith`, `prod_stage` gate)           |
| `src/dotenv.gleam`        | `.env` loading via `dot_env` (file values overwrite OS env)       |
| `src/http_helpers.gleam`  | Shared `httpc` send + status assertion + `post_json`              |
| `scripts/generate_sql.sh` | `squirrel` + `squirrel check` via `DATABASE_URL`                  |
| `gleam.toml`              | Manifest, Erlang target (`pog`, `gleam_time`, `gleam_otp`)        |
| `Dockerfile`              | Multi-stage build → Erlang shipment on `erlang:27-alpine`         |

```
twitch_announcer_gleam/
├── src/
│   ├── main.gleam      # stage dispatch + announce cycle
│   ├── decide.gleam    # pure decision logic
│   ├── db.gleam        # pog access + squirrel queries
│   ├── sql.gleam       # generated (do not hand-edit)
│   ├── sql/            # fetch_enabled, mark_* queries
│   ├── twitch.gleam    # Twitch API client
│   ├── discord.gleam   # Discord webhooks
│   ├── dotenv.gleam    # .env loading
│   └── http_helpers.gleam  # httpc helpers + post_json
├── scripts/
│   └── generate_sql.sh # local SQL regen
├── test/               # gleeunit tests + fixtures/c3_fixture.sql
├── gleam.toml          # manifest (target = erlang)
├── Dockerfile          # build + runtime images
├── README.md           # user-facing docs
└── AGENTS.md           # this file
```

### Env

| Name                                                 | Notes                                                                    |
| ---------------------------------------------------- | ------------------------------------------------------------------------ |
| `STAGE`                                              | `BUILD` (skip) / `DEV` (once) / `PROD` (forever); anything else panics   |
| `POSTGRES_CONNECTION_STRING`                         | Required at runtime (`DEV`/`PROD`); parsed for `pog` pool config         |
| `TWITCH_APP_ID` / `TWITCH_APP_SECRET`                | Required Twitch credentials                                              |
| `OFFLINE_GRACE_TIME`                                 | Optional, default `1800`; invalid/negative → `1800`                      |
| `PGHOST`/`PGPORT`/`PGUSER`/`PGPASSWORD`/`PGDATABASE` | Tests only: live-DB contract tests; skipped when absent                  |
| `DATABASE_URL`                                       | Tooling only: set from `POSTGRES_CONNECTION_STRING` by `generate_sql.sh` |

### CI (`.github/workflows/twitch_announcer_gleam.yml`)

On pushes/PRs touching `twitch_announcer_gleam/`, with a `postgres:16`
service: `gleam deps download` → `gleam build` → `gleam check` →
`gleam format --check src test` → load `test/fixtures/c3_fixture.sql`
via `psql` → `gleam test`. No DB codegen and no SQL drift check in CI —
regen locally with `./scripts/generate_sql.sh` before pushing query changes.

---

## 3. Constraints

- Never read or edit secrets (`*.env`, `*.key`, `*.secret`); use env var names only.
- Never touch `twitch_stream_announcer/` (legacy service) or commit changes.
- All SQL must stay parameterized (`ANY($1/$2)` via `pog`); never interpolate values.
- `decide.decide` must stay pure — no I/O, no env reads; side effects live in `main`/`db`/`discord`.
- DB writes happen in `PROD` only (`write_if_present`); keep that guard.
- Discord POSTs happen in `PROD` only (`post_announcements` + `prod_stage`); keep that guard.
- Never hand-edit `src/sql.gleam`; edit `src/sql/*.sql` and rerun `scripts/generate_sql.sh`.
- Keep docs (README, AGENTS.md) ≤200 lines each, verified against code.
