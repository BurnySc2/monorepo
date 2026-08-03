# FastAPI Server - Agent Reference

Compact reference for LLM agents. Target: scannable in <2 minutes.

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
| `src/main.py` | FastAPI app entry, router registration |
| `src/routes/` | 8 API routers (audiobook, login, raceroom, replay_*, tts_*) |
| `src/components/` | Business logic (audiobook, login, tts, replay_pack_builder) |
| `src/schemas/` | Pydantic models + Piccolo DB models |
| `src/s3_helper.py` | S3 operations (aioboto3) |
| `src/workers/` | Background workers (convert_audiobook, raceroom_fetch_records) |
| `src/models/` | Piccolo tables (raceroom, telegram_browser) |
| `src/queries/` | Raw SQL files |

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
from s3_helper import get_s3_client, object_upload, RUSTFS_AUDIOBOOK_BUCKET

async with get_s3_client() as s3:
    await object_upload(s3, RUSTFS_AUDIOBOOK_BUCKET, key, data)
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
from components.tts_generate import generate_audio
audio_bytes, duration = await generate_audio("edge", "voice_name", "Hello world")
# Engines: edge, kokoro, kitten, tiktok
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

**Excluded paths:** `**/workers/convert_audiobook.py`, `**/components/**`, `**/routes_/**`

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
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Specific file
pytest test/endpoints/login/test_login_twitch.py

# Specific test
pytest test/endpoints/login/test_login_twitch.py::test_twitch_login_start

# By marker
pytest -m endpoint     # endpoint tests only
pytest -m worker       # worker tests only
pytest -m "not slow"  # skip slow tests
```

### Key Fixtures (`test/conftest.py`)

```python
@pytest.fixture
def mock_s3_client():
    """Mock S3 client for tests."""
    # Use with: async with mock_s3_client() as s3: ...

@pytest.fixture
def auth_cookies():
    """Returns valid auth cookies for testing."""
    return {"twitch_access_token": "valid_test_token"}
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
uv run --directory src rio run --port 8000
```

### Run Workers
```bash
uv run --directory src python src/workers/convert_audiobook.py
uv run --directory src python src/workers/raceroom_fetch_records.py
```

### Database Migrations
```bash
piccolo migrations_new --app src
piccolo migrations_run --app src
```

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
