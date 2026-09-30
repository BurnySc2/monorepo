# FastAPI Server - Agent Reference

Compact reference for LLM agents. Target: scannable in <2 minutes.

> Single-source note: `src/main.py` (routers), `src/settings.py` (env/S3), `pyproject.toml` (ruff/pyrefly/pytest), `src/piccolo_conf.py` (DB), and `test/conftest.py` (fixtures) are authoritative; this file summarizes only.

---

## 1. Project Overview

Python FastAPI backend providing:
- **Audiobook TTS**: EPUB upload → audio conversion (Edge, Kokoro, Kitten, TikTok)
- **OAuth Auth**: Twitch, GitHub, Google login with cookie sessions
- **RaceRoom Stats**: Racing game best times tracking
- **SC2 Replays**: StarCraft II replay file parsing

Stack: FastAPI + async, PostgreSQL (Piccolo ORM), S3-compatible storage (RustFS)

---

## 2. Quick Reference

| Path | Purpose |
|------|---------|
| `src/main.py` | FastAPI app entry, router registration (9 routers, see below) |
| `src/routes/` | 9 API routers (audiobook, index, login, raceroom, replay_comparer, replay_parser, telegram_browser, tts_generate, tts_websocket) |
| `src/components/` | Business logic (audiobook, login, tts, replay_pack_builder) |
| `src/schemas/` | Pydantic API models + audiobook Piccolo tables (`audiobook/db_models.py`: AudiobookBook, AudiobookChapter) |
| `src/s3_helper.py` | S3 operations (aioboto3); bucket constants derive from `settings` (single source: `src/settings.py`) |
| `src/workers/` | Background workers (convert_audiobook, raceroom_fetch_records) |
| `src/models/` | Piccolo tables (raceroom: RRRE*, telegram_browser: Telegram*) |
| `src/queries/` | Raw SQL files |
| `src/settings.py` | Single source for env config (`Settings`); `src/piccolo_conf.py` uses `settings.postgres_connection_string` |

---

## 3. Key Patterns

### Router Registration
```python
app.include_router(login_router)                          # no prefix
app.include_router(TTSRouter, prefix="/tts-api")        # custom prefix
app.include_router(audiobook_router, prefix="/api/audiobook")
```

### Authenticated Routes
```python
from typing import Annotated
from fastapi import Depends
from components.login.cookies import LoggedInUser, get_current_user

@audiobook_router.get("/books")
async def list_books(
    current_user: Annotated[LoggedInUser, Depends(get_current_user)]
) -> list[BookListItem]:
    books = await AudiobookBook.objects().where(...)
```

### S3 Operations
```python
from s3_helper import get_s3_client, object_upload
from settings import settings

async with get_s3_client() as s3:
    await object_upload(s3, settings.rustfs_audiobook_bucket, key, data)
```

### Piccolo Queries
```python
# Simple
books = await AudiobookBook.objects().where(AudiobookBook.deleted == False)

# Raw SQL
query = (Path(__file__).parent.parent / "queries" / "audiobook_get_chapters.sql").read_text()
rows: list[dict] = await AudiobookChapter.raw(query, book_id, chapter_numbers)
```

### TTS Unified Interface
```python
from typing import cast

from components.tts_generate import generate_audio
from schemas.tts.engine import TTSEngine

audio_bytes, duration = await generate_audio(cast(TTSEngine, "edge"), "voice_label", "Hello world")
# Engines: edge, kokoro, kitten, tiktok (see schemas/tts/engine.py TTSEngine)
```

---

## 4. Code Style & Tooling

### Ruff (Lint + Format)

```bash
# Check
uv run ruff check src/

# Fix auto-fixable issues
uv run ruff check src/ --fix

# Format
uv run ruff format src/

# Run both (common workflow)
uv run ruff check src/ --fix && uv run ruff format src/
# From monorepo root: add --project fastapi_server (e.g. uv run --project fastapi_server ruff check src/)
```

**Key rules enforced:**
- **Q**: Double quotes enforced
- **I**: Import sorting
- **F**: Unused imports/variables
- **E/W**: Errors/warnings (PEP 8)
- **UP**: Pyupgrade (py310+)
- **C4**: Comprehensions
- **SIM**: Simplify (ignore SIM300)

**Config:** `line-length = 120`, `target-version = 'py310'`

### Pyrefly (Type Checking)

```bash
# Check types
uv run pyrefly check

# Check specific file
uv run pyrefly check src/routes/audiobook.py
```

**Excluded paths:** none in `src/` (only cache: `**/.venv/**`, `**/__pycache__/**`, `**/*.pyc`, `**/dist/**`; see `pyproject.toml [tool.pyrefly]`) — `convert_audiobook.py` is type-checked.

### SQLFluff (SQL Linting)

```bash
# Lint
uv run sqlfluff lint src/queries/

# Fix
uv run sqlfluff fix src/queries/
```

**Config:** `dialect = "postgres"`, `max_line_length = 120`, `param_style = "ampersand"` (`{var}`)

### Pre-commit Hooks

```bash
# Run on staged files
uv run pre-commit run

# Run on all files
uv run pre-commit run --all-files
```

**Hooks installed:**
| Hook | Purpose |
|------|---------|
| check-ast | Python syntax |
| check-yaml/toml | Config file validity |
| trailing-whitespace | Remove trailing spaces |
| pyupgrade | Upgrade to py310+ |
| ruff Q/fix | Double quotes |
| ruff F/fix | Remove unused |
| ruff I/fix | Sort imports |
| ruff-format | Format code |
| prettier | Format YAML |
| sqlfluff lint/fix | Lint/fix SQL |
| pyrefly | Type check |

### Style Rules Summary

- **Line length**: 120
- **Quotes**: Double only (`"..."` not `'...'`)
- **Python target**: 3.10+
- **Import sorting**: Ruff I rule (or `isort`)

---

## 5. Testing

```bash
# All tests (cwd is fastapi_server/)
uv run pytest

# With coverage
uv run pytest --cov=src --cov-report=term-missing

# Specific file
uv run pytest test/endpoints/login/test_login_twitch.py

# Specific test
uv run pytest test/endpoints/login/test_login_twitch.py::test_twitch_login_start

# By marker
uv run pytest -m endpoint     # endpoint tests only
uv run pytest -m worker       # worker tests only
uv run pytest -m "not slow"  # skip slow tests
```

### Key Fixtures (`test/conftest.py`)

```python
@pytest.fixture
def test_client() -> Iterator[TestClient]:
    """FastAPI TestClient without DB reset."""

@pytest.fixture
def test_client_db_reset() -> Iterator[TestClient]:
    """FastAPI TestClient with fresh Audiobook tables + mocked get_current_user."""

@pytest.fixture
def mock_s3(monkeypatch: pytest.MonkeyPatch) -> Iterator[AsyncMock]:
    """Mock S3 presigned URL + get_s3_client for audiobook routes (no network)."""
```

---

## 6. Environment Variables

Minimal set - see `.env.example` for full list:

```bash
# Database
POSTGRES_CONNECTION_STRING=postgresql://postgres:password@domain.com/db

# S3/RustFS
RUSTFS_S3_URL=http://localhost:9000
RUSTFS_AUDIOBOOK_BUCKET=rustfs-audiobook-bucket
RUSTFS_ACCESS_KEY=rustfsadmin
RUSTFS_SECRET_KEY=rustfsadmin

# OAuth (Twitch/GitHub/Google)
TWITCH_APP_CLIENT_ID=...
TWITCH_APP_CLIENT_SECRET=...

# Server
BACKEND_SERVER_URL=https://backend-domain.com
FRONTEND_URL=http://localhost:5173
STAGE=dev
```

---

## 7. Common Tasks

### Run Server (dev)
```bash
uv sync
uv run --directory src uvicorn main:app --host 0.0.0.0 --port 8000
# M6: Above assumes cwd=fastapi_server with PYTHONPATH=src (pytest sets pythonpath=src;
# Dockerfile sets ENV PYTHONPATH=/root/fastapi_server/src). From monorepo root use:
# uv run --project fastapi_server --directory fastapi_server/src uvicorn main:app --host 0.0.0.0 --port 8000
```

### Run Workers
```bash
# M6: cwd=fastapi_server; src/ prefix is required (do NOT add --directory src with src/ prefix).
PYTHONPATH=src uv run python src/workers/convert_audiobook.py
PYTHONPATH=src uv run python src/workers/raceroom_fetch_records.py
```

### Database Migrations
```bash
piccolo migrations_new --app src
piccolo migrations_run --app src
```
Config: `src/piccolo_conf.py` (`DB = PostgresEngine(config={"dsn": settings.postgres_connection_string})`); run with `PICCOLO_CONF=piccolo_conf` from `src/`.

### Add New Router
```python
# src/routes/example.py
from fastapi import APIRouter
example_router = APIRouter()

@example_router.get("/example")
async def get_example() -> dict:
    return {"message": "example"}
```
Then register in `main.py` with `app.include_router(example_router, prefix="/api")`

### Add DB Model
```python
# src/schemas/example/db_models.py
from piccolo.columns import Boolean, Integer, Text, Timestamp
from piccolo.table import Table

class ExampleTable(Table, tablename="example_table"):
    name = Text(required=True)
    value = Integer(default=0)
    active = Boolean(default=True)
```
Then run migrations (see above).
