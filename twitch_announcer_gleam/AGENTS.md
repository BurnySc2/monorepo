# Twitch Announcer Gleam - Agent Reference

Compact reference for LLM agents. Scannable in <2 minutes.

> Single-source note: `src/main.gleam` (stages, loop), `src/decide.gleam`
> (pure announce logic), `src/db.gleam` (Postgres via `pgo`), `gleam.toml`
> (deps), and `.github/workflows/twitch_announcer_gleam.yml` (CI) are
> authoritative; this file summarizes only.

---

## 1. Project Overview

Gleam (Erlang target) Twitch stream announcer:

- Polls Twitch API for enabled streams, posts Discord webhooks for newly-live
  ones, updates status in Postgres.
- `src/main.gleam`: stage dispatch — `BUILD` skips, `DEV` runs once with
  timing logs, `PROD` loops forever with 20 s sleep; DB writes only in `PROD`.
- `src/decide.gleam`: pure decision function
  `decide(rows, infos, now_epoch, grace_s)` → announced/online/offline/to-announce,
  honoring the offline grace window.
- `src/db.gleam`: `pgo` connection pool, `fetch_enabled`, `mark_announced` /
  `mark_online` / `mark_offline`.
- `src/twitch.gleam`, `src/discord.gleam`: external API clients.

Stack: Gleam on OTP 27 + PostgreSQL (`pgo` driver).

---

## 2. Quick Reference

| Command                         | Description                                           |
| ------------------------------- | ----------------------------------------------------- |
| `gleam deps download`           | Fetch dependencies (cwd is `twitch_announcer_gleam/`) |
| `gleam build`                   | Compile                                               |
| `gleam check`                   | Type-check                                            |
| `gleam format --check src test` | Format check (CI-enforced)                            |
| `gleam test`                    | Run `gleeunit` tests in `test/`                       |

| Path                | Purpose                                                                 |
| ------------------- | ----------------------------------------------------------------------- |
| `src/main.gleam`    | Entry `main`, `STAGE` dispatch, `run_once` cycle, `loop_forever` (20 s) |
| `src/decide.gleam`  | Pure announce-decision logic + time parsing/formatting                  |
| `src/db.gleam`      | `pgo` pool, parameterized queries, row mapping to `DbRow`               |
| `src/twitch.gleam`  | Twitch token + stream-info fetching                                     |
| `src/discord.gleam` | Discord webhook posting                                                 |
| `gleam.toml`        | Package manifest, Erlang target, dependency versions                    |
| `Dockerfile`        | Multi-stage build → Erlang shipment on `erlang:27-alpine`               |

```
twitch_announcer_gleam/
├── src/
│   ├── main.gleam      # stage dispatch + announce cycle
│   ├── decide.gleam    # pure decision logic
│   ├── db.gleam        # Postgres access
│   ├── twitch.gleam    # Twitch API client
│   └── discord.gleam   # Discord webhooks
├── test/               # gleeunit tests
├── gleam.toml          # manifest (target = erlang)
├── Dockerfile          # build + runtime images
├── README.md           # user-facing docs
└── AGENTS.md           # this file
```

### Env

| Name                                  | Notes                                                                  |
| ------------------------------------- | ---------------------------------------------------------------------- |
| `STAGE`                               | `BUILD` (skip) / `DEV` (once) / `PROD` (forever); anything else panics |
| `POSTGRES_CONNECTION_STRING`          | Required; parsed for pool config                                       |
| `TWITCH_APP_ID` / `TWITCH_APP_SECRET` | Required Twitch credentials                                            |
| `OFFLINE_GRACE_TIME`                  | Optional, default `1800`; invalid/negative → `1800`                    |

---

## 3. Constraints

- Never read or edit secrets (`*.env`, `*.key`, `*.secret`); use env var names only.
- Never touch `twitch_stream_announcer/` (legacy service) or commit changes.
- All SQL must stay parameterized (`$1`, `$2` via `pgo`); never interpolate values.
- `decide.decide` must stay pure — no I/O, no env reads; side effects live in `main`/`db`.
- DB writes happen in `PROD` only (`write_if_present`); keep that guard.
- Keep docs (README, AGENTS.md) ≤200 lines each, verified against code.
