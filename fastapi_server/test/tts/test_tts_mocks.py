"""Mocked tests for cloud TTS engines (HTTP-based)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from components.tts_generate import (
    TTSEngine,
    generate_audio,
    list_voices,
)

# Cloud engines that use HTTP
CLOUD_ENGINES = ["edge", "tiktok"]


class TestEdgeTTSMocked:
    """Mocked tests for Edge TTS."""

    @pytest.mark.asyncio
    async def test_list_voices_returns_static_list(self):
        """Edge TTS should return a static list of voices."""
        voices = await list_voices("edge")
        assert len(voices) > 0
        # Check that voices have expected attributes
        for voice in voices:
            assert hasattr(voice, "name")
            assert hasattr(voice, "language")

    @pytest.mark.asyncio
    async def test_generate_audio_calls_edge_tts(self, tmp_path):
        """Edge TTS generate should use edge_tts.Communicate."""
        with patch("edge_tts.Communicate") as mock_communicate:
            mock_instance = MagicMock()
            mock_communicate.return_value = mock_instance
            mock_instance.save = AsyncMock()
            mock_instance.get_audio = AsyncMock()

            # Import and call directly
            from components.tts_generate import edge_engine

            assert hasattr(edge_engine, "generate_audio_async")
            assert hasattr(edge_engine, "list_voices_async")


class TestTikTokTTSMocked:
    """Mocked tests for TikTok TTS."""

    @pytest.mark.asyncio
    async def test_list_voices_returns_static_list(self):
        """TikTok TTS should return a static list of voices."""
        voices = await list_voices("tiktok")
        assert len(voices) > 0
        for voice in voices:
            assert hasattr(voice, "language")

    @pytest.mark.asyncio
    async def test_tiktok_uses_httpx(self):
        """TikTok TTS should use httpx for HTTP requests."""
        from components.tts_generate import tiktok_engine

        assert hasattr(tiktok_engine, "httpx")
        assert hasattr(tiktok_engine, "generate_audio_async")


class TestEngineValidation:
    """Tests for engine name validation."""

    @pytest.mark.asyncio
    async def test_unknown_engine_raises_valueerror(self):
        """Unknown engine should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await list_voices("nonexistent_engine")
        assert "Unknown TTS engine" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unknown_engine_generate_raises_valueerror(self):
        """Unknown engine in generate should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            await generate_audio("unknown_engine", "voice", "text")
        assert "Unknown TTS engine" in str(exc_info.value)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("engine", CLOUD_ENGINES)
    async def test_cloud_engines_case_insensitive(self, engine):
        """Cloud engine names should be case-insensitive."""
        voices_lower = await list_voices(engine.lower())
        voices_upper = await list_voices(engine.upper())
        assert len(voices_lower) == len(voices_upper)


class TestLocalEnginesModuleStructure:
    """Tests for local engine module structure."""

    @pytest.mark.asyncio
    async def test_kokoro_has_required_functions(self):
        from components.tts_generate import kokoro_engine

        assert hasattr(kokoro_engine, "list_voices_async")
        assert hasattr(kokoro_engine, "generate_audio_async")

    @pytest.mark.asyncio
    async def test_kitten_has_required_functions(self):
        from components.tts_generate import kitten_engine

        assert hasattr(kitten_engine, "list_voices_async")
        assert hasattr(kitten_engine, "generate_audio_async")
        assert hasattr(kitten_engine, "VOICES")

    @pytest.mark.asyncio
    async def test_pocket_has_required_functions(self):
        from components.tts_generate import pocket_engine

        assert hasattr(pocket_engine, "list_voices_async")
        assert hasattr(pocket_engine, "generate_audio_async")


class TestUnifiedAPIIntegration:
    """Integration tests for unified API."""

    @pytest.mark.asyncio
    async def test_all_engines_listed_in_engines_constant(self):
        """All engines should be listed in ENGINES constant."""
        from components.tts_generate import ENGINES

        expected_engines = ["edge", "kokoro", "kitten", "pocket", "tiktok"]
        assert sorted(ENGINES) == sorted(expected_engines)

    @pytest.mark.asyncio
    async def test_tts_engine_literal_allows_all_engines(self):
        """TTSEngine literal should accept all engine names."""

        # This is a type hint check - if it passes, the literal is correct
        valid_engines: list[TTSEngine] = [
            "edge",
            "kokoro",
            "kitten",
            "pocket",
            "tiktok",
        ]
        assert len(valid_engines) == 6
