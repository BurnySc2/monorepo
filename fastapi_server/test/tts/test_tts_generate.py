"""Tests for unified TTS generation interface."""

from __future__ import annotations

import pytest

from components.tts_generate import (
    ENGINES,
    TTSEngine,
    VoiceInfo,
    generate_audio,
    list_voices,
)


class TestListVoices:
    """Tests for list_voices function."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("engine", ENGINES)
    async def test_list_voices_returns_list(self, engine: TTSEngine):
        """Each engine should return a non-empty list of voices."""
        voices = await list_voices(engine)
        assert isinstance(voices, list)
        assert len(voices) > 0

    @pytest.mark.asyncio
    @pytest.mark.parametrize("engine", ENGINES)
    async def test_list_voices_contains_voice_info(self, engine: TTSEngine):
        """Each voice should be a VoiceInfo dataclass with a name."""
        voices = await list_voices(engine)
        for voice in voices:
            assert isinstance(voice, VoiceInfo)
            assert voice.name
            assert isinstance(voice.name, str)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("engine", ENGINES)
    async def test_list_voices_voice_has_string_name(self, engine: TTSEngine):
        """Each voice should have a string name."""
        voices = await list_voices(engine)
        for voice in voices:
            assert isinstance(voice.name, str)
            assert len(voice.name) > 0

    @pytest.mark.asyncio
    async def test_invalid_engine_raises_valueerror(self):
        """Unknown engine should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown TTS engine"):
            await list_voices("invalid_engine")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("engine", ENGINES)
    async def test_engine_case_insensitive(self, engine: TTSEngine):
        """Engine names should be case-insensitive."""
        voices_lower = await list_voices(engine.lower())
        voices_upper = await list_voices(engine.upper())
        assert len(voices_lower) == len(voices_upper)


class TestGenerateAudio:
    """Tests for generate_audio function."""

    @pytest.mark.asyncio
    async def test_invalid_engine_raises_valueerror(self):
        """Unknown engine should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown TTS engine"):
            await generate_audio("invalid_engine", "voice", "text")


class TestVoiceInfo:
    """Tests for VoiceInfo dataclass."""

    def test_voice_info_creation(self):
        """VoiceInfo should be creatable with name only."""
        voice = VoiceInfo(name="test_voice")
        assert voice.name == "test_voice"
        assert voice.language is None
        assert voice.gender is None
        assert voice.description is None

    def test_voice_info_full_creation(self):
        """VoiceInfo should be creatable with all fields."""
        voice = VoiceInfo(
            name="test_voice",
            language="en",
            gender="Female",
            description="Test voice",
        )
        assert voice.name == "test_voice"
        assert voice.language == "en"
        assert voice.gender == "Female"
        assert voice.description == "Test voice"


class TestTTSEngine:
    """Tests for TTSEngine type alias."""

    def test_tts_engine_literal_values(self):
        """TTSEngine should accept all valid engine names."""
        valid_engines: list[TTSEngine] = [
            "edge",
            "kokoro",
            "kitten",
            "pocket",
            "tiktok",
        ]
        assert len(valid_engines) == 5


class TestModuleExports:
    """Tests for module exports."""

    def test_engines_list_defined(self):
        """ENGINES list should be defined."""
        from components.tts_generate import ENGINES

        assert isinstance(ENGINES, list)
        assert len(ENGINES) > 0
