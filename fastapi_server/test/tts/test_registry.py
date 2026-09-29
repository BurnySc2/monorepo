"""Offline tests for TTS ENGINE_REGISTRY dispatch."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

import components.tts_generate as tts
from components.tts_generate import ENGINE_REGISTRY, generate_audio, list_all_voices, list_voices
from schemas.tts import VoiceInfo


def _voice(engine: str, label: str) -> VoiceInfo:
    return VoiceInfo(
        engine=engine,  # type: ignore[arg-type]
        internal_name=f"{engine}-{label}",
        label=label,
        gender="Female",
        locale="en-us",
    )


class TestEngineRegistry:
    def test_registry_keys(self):
        assert set(ENGINE_REGISTRY) == {"edge", "kokoro", "kitten", "tiktok"}

    def test_registry_modules_expose_api(self):
        for module in ENGINE_REGISTRY.values():
            assert hasattr(module, "list_voices_async")
            assert hasattr(module, "generate_audio_async")

    @pytest.mark.asyncio
    async def test_list_voices_dispatches_via_registry(self):
        mock_module = AsyncMock()
        mock_module.list_voices_async.return_value = [_voice("edge", "Aria")]
        with patch.dict(ENGINE_REGISTRY, {"edge": mock_module}):
            voices = await list_voices("edge")  # type: ignore[arg-type]
        assert len(voices) == 1
        mock_module.list_voices_async.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_voices_unknown_engine_message(self):
        with pytest.raises(ValueError, match="Unknown TTS engine"):
            await list_voices("nope")  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_list_voices_unknown_message_identical(self):
        try:
            await list_voices("nope")  # type: ignore[arg-type]
        except ValueError as e:
            assert str(e) == "Unknown TTS engine: nope. Supported engines: edge, kokoro, kitten, tiktok"
        else:  # pragma: no cover
            raise AssertionError("expected ValueError")

    @pytest.mark.asyncio
    async def test_list_all_voices_single_pass(self):
        tts._all_voices_cache.clear()
        tts._label_to_voice_info = {}
        calls: list[str] = []

        async def fake_list_voices(engine):  # type: ignore[no-untyped-def]
            calls.append(engine)
            return [_voice(engine, f"Voice-{engine}")]

        with patch("components.tts_generate.list_voices", side_effect=fake_list_voices):
            result = await list_all_voices()

        # One call per engine (single pass populates result + label map)
        assert sorted(calls) == sorted(["edge", "kokoro", "kitten", "tiktok"])
        assert len(result) == 4
        # Label map populated without a second pass
        assert tts._label_to_voice_info[("edge", "voice-edge")].internal_name == "edge-Voice-edge"
        tts._all_voices_cache.clear()
        tts._label_to_voice_info = {}

    @pytest.mark.asyncio
    async def test_generate_audio_dispatches_via_registry(self):
        tts._all_voices_cache.clear()
        tts._label_to_voice_info = {("edge", "aria"): _voice("edge", "Aria")}
        mock_module = AsyncMock()
        mock_module.generate_audio_async.return_value = (b"ID3fake", 1.0)

        async def fake_list_all():  # type: ignore[no-untyped-def]
            return [_voice("edge", "Aria")]

        fake_mp3 = AsyncMock()
        fake_mp3.info.length = 2.5
        with (
            patch.dict(ENGINE_REGISTRY, {"edge": mock_module}),
            patch("components.tts_generate.list_all_voices", side_effect=fake_list_all),
            patch("components.tts_generate.MP3", return_value=fake_mp3),
        ):
            audio_bytes, duration = await generate_audio("edge", "aria", "hello")  # type: ignore[arg-type]

        assert audio_bytes == b"ID3fake"
        assert duration == 2.5
        mock_module.generate_audio_async.assert_awaited_once()
        tts._all_voices_cache.clear()
        tts._label_to_voice_info = {}

    @pytest.mark.asyncio
    async def test_generate_audio_unknown_engine_message_identical(self):
        try:
            await generate_audio("nope", "voice", "text")  # type: ignore[arg-type]
        except ValueError as e:
            assert str(e) == "Unknown TTS engine: nope. Supported engines: edge, kokoro, kitten, tiktok"
        else:  # pragma: no cover
            raise AssertionError("expected ValueError")
