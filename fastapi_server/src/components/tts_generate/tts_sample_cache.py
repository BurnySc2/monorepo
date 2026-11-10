"""Disk cache for canonical TTS sample audio."""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import uuid
from contextlib import suppress
from io import BytesIO
from pathlib import Path

from loguru import logger
from mutagen import MutagenError
from mutagen.mp3 import MP3

from settings import settings

SAMPLE_TEXT_VERSION = 2

MAX_TEXT_LENGTH = 1500
MAX_CACHED_FILES = 200
MAX_CACHED_BYTES = 200 * 1024 * 1024
MAX_KEY_LOCKS = 500

CANONICAL_TEXT_HASHES: set[str] = set()

_key_locks: dict[str, asyncio.Lock] = {}

_SANITIZE_RE = re.compile(r"[^a-z0-9]+")


def _sanitize(value: str) -> str:
    cleaned = _SANITIZE_RE.sub("_", value.lower()).strip("_")[:30].strip("_")
    return cleaned or "unknown"


def resolve_samples_dir() -> Path:
    configured = settings.tts_samples_dir or "./data/tts_samples"
    candidate = Path(configured)
    if not candidate.is_absolute():
        candidate = Path(__file__).parents[3] / candidate
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def sample_cache_key(engine: str, normalized_label: str, text: str) -> str:
    san_engine = _sanitize(engine)
    san_label = _sanitize(normalized_label)
    digest = hashlib.sha256(
        f"{engine.lower()}|{normalized_label.lower()}|{SAMPLE_TEXT_VERSION}|{text}".encode()
    ).hexdigest()[:16]
    return f"{san_engine}_{san_label}_v{SAMPLE_TEXT_VERSION}_{digest}.mp3"


def get_key_lock(key: str) -> asyncio.Lock:
    lock = _key_locks.get(key)
    if lock is None:
        if len(_key_locks) >= MAX_KEY_LOCKS:
            _key_locks.pop(next(iter(_key_locks)))
        lock = asyncio.Lock()
        _key_locks[key] = lock
    return lock


# TODO(allowlist): replace length check with hash allowlist of canonical texts.
def is_canonical_sample(text: str) -> bool:
    return 20 <= len(text) <= MAX_TEXT_LENGTH


def _read_validated(path: Path) -> bytes | None:
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return None
    try:
        audio = MP3(BytesIO(data))
    except MutagenError:
        with suppress(OSError):
            path.unlink(missing_ok=True)
        return None
    if audio.info is None:
        with suppress(OSError):
            path.unlink(missing_ok=True)
        return None
    return data


def _validate_mp3(data: bytes) -> None:
    try:
        audio = MP3(BytesIO(data))
    except MutagenError as exc:
        raise ValueError("Invalid MP3 data") from exc
    if audio.info is None:
        raise ValueError("Invalid MP3 data")


def _write_tmp_and_replace(target: Path, data: bytes) -> None:
    tmp = target.parent / f"tmp.{os.getpid()}.{uuid.uuid4().hex}.tmp"
    tmp.write_bytes(data)
    tmp.replace(target)


def _enforce_disk_caps(directory: Path) -> None:
    try:
        candidates = [p for p in directory.glob("*.mp3") if p.is_file()]
    except OSError as exc:
        logger.warning(f"Failed to list samples for cap enforcement: {exc}")
        return
    aged: list[tuple[float, int, Path]] = []
    total = 0
    for path in candidates:
        with suppress(OSError):
            stat = path.stat()
            aged.append((stat.st_mtime, stat.st_size, path))
            total += stat.st_size
    if len(aged) < MAX_CACHED_FILES and total <= MAX_CACHED_BYTES:
        return
    aged.sort(key=lambda item: item[0])
    while aged and (len(aged) >= MAX_CACHED_FILES or total > MAX_CACHED_BYTES):
        _, size, oldest = aged.pop(0)
        try:
            oldest.unlink()
        except OSError as exc:
            logger.warning(f"Failed to evict cached sample {oldest.name}: {exc}")
            continue
        total -= size


async def read_cached(key: str) -> bytes | None:
    if "/" in key or "\\" in key or ".." in key:
        return None
    path = resolve_samples_dir() / key
    return await asyncio.to_thread(_read_validated, path)


async def write_cached_atomic(key: str, data: bytes) -> Path:
    await asyncio.to_thread(_validate_mp3, data)
    target = resolve_samples_dir() / key
    await asyncio.to_thread(_enforce_disk_caps, target.parent)
    await asyncio.to_thread(_write_tmp_and_replace, target, data)
    return target


def clear_samples_dir() -> int:
    directory = resolve_samples_dir()
    resolved = directory.resolve()
    if resolved.name != "tts_samples" or resolved in (Path("/"), Path("/data")):
        logger.warning(f"Refusing to clear unexpected samples dir: {resolved}")
        return 0
    removed = 0
    for pattern in ("*.mp3", "*.tmp", "*.json"):
        try:
            matches = list(directory.glob(pattern))
        except OSError as exc:
            logger.warning(f"Failed to list {pattern} in samples dir: {exc}")
            continue
        for path in matches:
            try:
                if path.is_file():
                    path.unlink()
                    removed += 1
            except OSError as exc:
                logger.warning(f"Failed to remove cached sample {path.name}: {exc}")
    return removed
