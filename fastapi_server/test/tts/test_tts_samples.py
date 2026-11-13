"""Minimal critical tests for TTS sample disk cache."""

from __future__ import annotations

import re

import pytest
from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st

from components.tts_generate.tts_sample_cache import (
    clear_samples_dir,
    is_canonical_sample,
    read_cached,
    resolve_samples_dir,
    sample_cache_key,
)
from settings import settings

SAMPLE_TEXT = "Hello world, this is a canonical sample text."


@pytest.mark.asyncio
async def test_traversal_voice_stays_hex_only_and_never_escapes(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "tts_samples_dir", str(tmp_path))
    key = sample_cache_key("edge", "../../etc", SAMPLE_TEXT)
    assert re.fullmatch(r"[a-z0-9_]+\.mp3", key)
    assert await read_cached("../../etc/passwd.mp3") is None
    assert await read_cached("..\\evil.mp3") is None
    assert await read_cached("a/b.mp3") is None
    assert (resolve_samples_dir() / key).resolve().is_relative_to(resolve_samples_dir().resolve())
    assert list(tmp_path.iterdir()) == []


@pytest.mark.asyncio
async def test_corrupt_cached_file_returns_none_and_unlinks(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "tts_samples_dir", str(tmp_path))
    key = sample_cache_key("edge", "aria", SAMPLE_TEXT)
    target = tmp_path / key
    target.write_bytes(b"not an mp3 at all, just garbage bytes")
    assert await read_cached(key) is None
    assert not target.exists()


def test_clear_samples_dir_happy_path_and_refusal(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "tts_samples_dir", str(tmp_path))
    (tmp_path / "a.mp3").write_bytes(b"x")
    assert clear_samples_dir() == 0
    assert (tmp_path / "a.mp3").exists()
    samples_dir = tmp_path / "tts_samples"
    samples_dir.mkdir()
    monkeypatch.setattr(settings, "tts_samples_dir", str(samples_dir))
    for name in ("a.mp3", "b.tmp", "c.json"):
        (samples_dir / name).write_bytes(b"x")
    keeper = samples_dir / "keep.txt"
    keeper.write_bytes(b"keep")
    assert clear_samples_dir() == 3
    assert keeper.exists()
    assert list(samples_dir.glob("*.mp3")) == []


@given(engine=st.text(max_size=50), label=st.text(max_size=50))
@hyp_settings(max_examples=30, deadline=None)
def test_sample_cache_key_always_safe_and_deterministic(engine: str, label: str) -> None:
    first = sample_cache_key(engine, label, SAMPLE_TEXT)
    assert sample_cache_key(engine, label, SAMPLE_TEXT) == first
    assert re.fullmatch(r"[a-z0-9_]+\.mp3", first)
    assert re.fullmatch(r"[0-9a-f]{16}", first.rsplit("_", 1)[-1].removesuffix(".mp3"))


@given(text=st.text(max_size=2000))
@hyp_settings(max_examples=30, deadline=None)
def test_is_canonical_matches_length_bounds(text: str) -> None:
    assert is_canonical_sample(text) == (20 <= len(text) <= 1500)
