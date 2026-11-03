# twitch_announcer_gleam

Gleam (Erlang target) port of the Twitch stream announcer. It polls the
Twitch API for enabled streams, decides which newly-live streams to announce,
posts Discord webhooks, and updates stream status in Postgres.

## Behavior

Entry point is `main` in `src/main.gleam`, driven by the `STAGE` env var:

| `STAGE` | Behavior                                                         |
| ------- | ---------------------------------------------------------------- |
| `BUILD` | Prints a skip message and exits (no DB, no API calls)            |
| `DEV`   | Runs the announce cycle exactly once, with per-phase timing logs |
| `PROD`  | Runs the cycle forever, sleeping 20 s between iterations         |

Each cycle (`run_once` in `src/main.gleam`):

1. Fetches enabled rows from Postgres (`db.fetch_enabled`).
2. Gets a Twitch app access token and live stream info for the distinct names.
3. Calls `decide.decide` (pure logic in `src/decide.gleam`) to split rows into
   announced / online / now-offline / to-announce.
4. Writes status updates back to the DB — but only in `PROD`
   (`write_if_present` skips writes otherwise).
5. Posts Discord webhooks for newly-live streams.

Failures in a cycle are logged (`run_once failed: ...`); the `PROD` loop
continues with the next iteration.

## Environment variables

| Name                         | Required | Default | Notes                                                                                                                                               |
| ---------------------------- | -------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `STAGE`                      | yes      | —       | Must be `BUILD`, `DEV`, or `PROD`; anything else panics                                                                                             |
| `POSTGRES_CONNECTION_STRING` | yes      | —       | Parsed for host/port/user/password/database; missing value panics                                                                                   |
| `TWITCH_APP_ID`              | yes      | —       | Twitch client ID; missing value panics                                                                                                              |
| `TWITCH_APP_SECRET`          | yes      | —       | Twitch client secret; missing value panics                                                                                                          |
| `OFFLINE_GRACE_TIME`         | no       | `1800`  | Seconds since `last_seen_online` before a stream may be re-announced; unparsable or negative values fall back to `1800` (see `parse_grace_seconds`) |

## How to run

Requires Gleam 1.19.2+ with OTP 27 (see CI workflow).

```bash
cd twitch_announcer_gleam

# Download dependencies
gleam deps download

# Build and type-check
gleam build
gleam check

# Run tests
gleam test

# Run once (DEV) or forever (PROD) depending on STAGE
STAGE=DEV POSTGRES_CONNECTION_STRING=... TWITCH_APP_ID=... TWITCH_APP_SECRET=... gleam run
```

Format check (enforced in CI):

```bash
gleam format --check src test
```

## Docker

Multi-stage `Dockerfile`: builds with the `ghcr.io/gleam-lang/gleam`
Erlang image and exports an Erlang shipment onto an `erlang:27-alpine`
runtime image (with `libpq` for Postgres parity). The entrypoint script
runs the shipped `run` command.

```bash
docker build -t twitch_announcer_gleam ./twitch_announcer_gleam
```

## CI

`Test Twitch Announcer Gleam` (`.github/workflows/twitch_announcer_gleam.yml`):
triggers on pushes/PRs touching `twitch_announcer_gleam/` — sets up
OTP 27 + Gleam 1.19.2, then `gleam deps download`, `gleam build`,
`gleam check`, `gleam format --check src test`, `gleam test`, plus a live
Postgres decoder smoke step against `postgres:16`.
