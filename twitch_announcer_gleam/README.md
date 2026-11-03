# twitch_announcer_gleam

Gleam (Erlang target) port of the Twitch stream announcer. It polls the
Twitch API for enabled streams, decides which newly-live streams to announce,
posts Discord webhooks, and updates stream status in Postgres.

## Behavior

Entry point is `main` in `src/main.gleam`, driven by the `STAGE` env var:

| `STAGE` | Behavior                                              |
| ------- | ----------------------------------------------------- |
| `BUILD` | Prints a skip message and exits (no DB, no API calls) |
| `DEV`   | Runs the announce cycle exactly once                  |
| `PROD`  | Runs the cycle forever, sleeping 20 s between runs    |

Anything else panics. Logging is plain `io.println` (no logging library):
startup line, `Running once` per iteration, one `Updating ...` line per
non-empty status list, and `run_once failed: ...` on cycle failure — there
are no per-stage timing logs. A failing cycle is logged and the `PROD` loop
continues with the next iteration.

Each cycle (`run_once` in `src/main.gleam`):

1. Fetches enabled rows from Postgres (`db.fetch_enabled`, via the
   squirrel-generated `sql.fetch_enabled` on a `pog` pool).
2. Gets a Twitch app access token and live stream info for the distinct
   names (lowercased, batched 20 per Helix request in `src/twitch.gleam` —
   `chunks` wraps `list.sized_chunk`, all sends go through the shared
   `http_helpers.send`).
3. Calls `decide.decide` (pure logic in `src/decide.gleam`, using `birl`
   for time parsing and `humanize` for age strings) to split rows into
   announced / online / now-offline / to-announce, honoring the offline
   grace window.
4. Writes status updates back through table-driven `update_entries`
   (announced / online / now-offline triples applied with `list.try_each`,
   stamped with `utc_now`, a `gleam_time` `Timestamp`) — but only in `PROD`
   (`write_if_present` skips writes otherwise).
5. Handles Discord announcements for newly-live streams — real webhook
   POSTs (built with `kitazith` embeds, delivered via `post_json` in
   `src/http_helpers.gleam`) only in `PROD` (gated on the `prod_stage`
   const in `src/discord.gleam`); otherwise the payload is only logged.

## Environment variables

Runtime (read via `envoy` in `src/main.gleam` / `src/db.gleam`):

| Name                         | Required | Default | Notes                                                                                                                                               |
| ---------------------------- | -------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `STAGE`                      | yes      | —       | Must be `BUILD`, `DEV`, or `PROD`; anything else panics                                                                                             |
| `POSTGRES_CONNECTION_STRING` | yes      | —       | `pog.url_config` pool URL for `DEV`/`PROD`; missing value panics                                                                                    |
| `TWITCH_APP_ID`              | yes      | —       | Twitch client ID; missing value panics                                                                                                              |
| `TWITCH_APP_SECRET`          | yes      | —       | Twitch client secret; missing value panics                                                                                                          |
| `OFFLINE_GRACE_TIME`         | no       | `1800`  | Seconds since `last_seen_online` before a stream may be re-announced; unparsable or negative values fall back to `1800` (see `parse_grace_seconds`) |

Tests only (`test/db_contract_test.gleam` builds a live URL from these;
tests are skipped when they are absent):

| Name                                                     | Notes                                         |
| -------------------------------------------------------- | --------------------------------------------- |
| `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` | Live-DB contract tests; set by CI (see below) |

Tooling only (not read at runtime):

| Name           | Notes                                                                                                                   |
| -------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `DATABASE_URL` | Connection string for `squirrel` typed-SQL codegen; `scripts/generate_sql.sh` sets it from `POSTGRES_CONNECTION_STRING` |

## How to run

Requires Gleam 1.19.2 with OTP 27 (see CI workflow).

On startup `main` calls `dotenv.load_dotenv` (`src/dotenv.gleam`,
via `dot_env`), which loads `.env` and `twitch_announcer_gleam/.env`
when present — file values overwrite OS env. Copy `.env.example` to
`.env` and fill in values (never commit real secrets).

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

Regenerate the checked-in SQL bindings after editing `src/sql/*.sql`
(local only — needs a live DB, never runs in CI):

```bash
./scripts/generate_sql.sh
```

Format check (enforced in CI):

```bash
gleam format --check src test
```

## Structure

```
twitch_announcer_gleam/
├── src/
│   ├── main.gleam        # stage dispatch + announce cycle (table-driven update_entries)
│   ├── decide.gleam      # pure decision logic (birl + humanize)
│   ├── db.gleam          # pog pool + squirrel queries, Timestamp <-> String mapping
│   ├── sql.gleam         # checked-in squirrel output (do not hand-edit)
│   ├── sql/              # fetch_enabled, mark_announced, mark_online, mark_offline
│   ├── twitch.gleam      # Twitch token + stream-info fetching (sized_chunk, shared send)
│   ├── discord.gleam     # Discord webhooks via kitazith (prod_stage gate)
│   ├── dotenv.gleam      # .env loading via dot_env
│   └── http_helpers.gleam# shared httpc send + status check + post_json
├── scripts/
│   └── generate_sql.sh   # local squirrel regen (squirrel + squirrel check)
├── test/
│   ├── *_test.gleam      # gleeunit unit + contract tests
│   └── fixtures/c3_fixture.sql  # smoke rows for DB contract tests
├── gleam.toml            # manifest (target = erlang; pog, gleam_time, gleam_otp)
├── Dockerfile            # build + runtime images
├── README.md             # user-facing docs
└── AGENTS.md             # agent reference
```

`gleam.toml` runtime deps include `pog` (Postgres), `gleam_time`
(`Timestamp`), and `gleam_otp` (actor pool); `squirrel` is a
dev-dependency for codegen only. There is no `pgo` usage left and no
logging library — output goes through `io.println`.

## SQL codegen

`src/sql/*.sql` are the sources of truth; `src/sql.gleam` is generated.
`fetch_enabled` uses `COALESCE` defaults (`''` / `'offline'`), and the
`mark_*` writes use parameterized `twitch_name = ANY($1/$2)` lists via
`pog`. Regenerate locally with `./scripts/generate_sql.sh` before
pushing query changes — CI performs no drift check.

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
OTP 27 + Gleam 1.19.2, then:

1. `gleam deps download`, `gleam build`, `gleam check`
2. `gleam format --check src test`
3. Loads `test/fixtures/c3_fixture.sql` via `psql` against a
   `postgres:16` service (env `PGHOST`/`PGPORT`/`PGUSER`/`PGPASSWORD`/`PGDATABASE`)
4. `gleam test` (skips live-DB contract tests when `PG*` vars are absent)

## Constraints

- Never read or edit real secrets (`*.env`, `*.key`, `*.secret`); use
  env var names only.
- All SQL must stay parameterized (`ANY($1/$2)` via `pog`); never
  interpolate values.
- `decide.decide` must stay pure — no I/O, no env reads; side effects
  live in `main`/`db`/`discord`.
- Never hand-edit `src/sql.gleam`; change `src/sql/*.sql` and rerun
  `scripts/generate_sql.sh`.
