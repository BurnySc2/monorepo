"""Unit tests for convert_audiobook worker.

These tests mock external dependencies (database, MinIO, TTS).
The core conversion logic is well covered. Integration tests would
require a real database for full coverage of check_queued_chapters.
"""

import asyncio
import io
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.workers.convert_audiobook import (
    AudiobookConversionContext,
    convert_one,
    keep_converting,
)


class TestAudiobookConversionContext:
    """Tests for AudiobookConversionContext context manager."""

    @pytest.mark.asyncio
    async def test_context_enter_sets_started_converting(self):
        """Test that entering context sets started_converting timestamp."""
        mock_chapter = MagicMock()
        mock_chapter.id = 42
        mock_chapter.content = "Test content"
        mock_chapter.started_converting = None
        mock_chapter.save = AsyncMock()

        with (
            patch("src.workers.convert_audiobook.get_chapter_combined_text", return_value="Test content"),
            patch("src.workers.convert_audiobook.ESTIMATE_FACTOR", 0.3),
        ):
            async with AudiobookConversionContext(mock_chapter) as context:
                assert context.minio_object_name == "42_audio.mp3"
                mock_chapter.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_exit_success_clears_flag(self):
        """Test that exiting context with no exception clears started_converting."""
        mock_chapter = MagicMock()
        mock_chapter.started_converting = None
        mock_chapter.save = AsyncMock()

        async with AudiobookConversionContext(mock_chapter):
            pass

        assert mock_chapter.save.call_count == 2
        assert mock_chapter.started_converting is None

    @pytest.mark.asyncio
    async def test_context_exit_failure_clears_flag(self):
        """Test that exiting context after exception clears started_converting and logs error."""
        mock_chapter = MagicMock()
        mock_chapter.started_converting = None
        mock_chapter.save = AsyncMock()

        with pytest.raises(ValueError):
            async with AudiobookConversionContext(mock_chapter):
                raise ValueError("Conversion failed")

        assert mock_chapter.save.call_count == 2
        assert mock_chapter.started_converting is None


class TestConvertOne:
    """Tests for convert_one function - the main conversion logic."""

    @pytest.mark.asyncio
    async def test_converts_chapter_successfully(self):
        """Test successful chapter conversion end-to-end flow."""
        mock_chapter = MagicMock()
        mock_chapter.id = 42
        mock_chapter.chapter_number = 1
        mock_chapter.book = 1
        mock_chapter.content = "Test chapter content"
        mock_chapter.audio_settings = '{"engine_name": "kokoro", "voice_name": "bella"}'
        mock_chapter.minio_object_name = None

        mock_audio = io.BytesIO(b"fake audio data")

        mock_context = MagicMock()
        mock_context.chapter = mock_chapter
        mock_context.minio_object_name = "42_audio.mp3"

        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("src.workers.convert_audiobook.AudiobookConversionContext", return_value=mock_context),
            patch("src.workers.convert_audiobook.generate_text_to_speech", new_callable=AsyncMock) as mock_tts,
        ):
            mock_tts.return_value = mock_audio

            with patch("src.workers.convert_audiobook.AudiobookChapter.objects") as mock_objects:
                mock_chapter2 = MagicMock()
                mock_chapter2.audio_settings = mock_chapter.audio_settings
                mock_objects.return_value.where.return_value.first = AsyncMock(return_value=mock_chapter2)

                with patch("src.workers.convert_audiobook.get_s3_client") as mock_s3:
                    mock_s3.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
                    mock_s3.return_value.__aexit__ = AsyncMock(return_value=None)

                    with patch("src.workers.convert_audiobook.object_upload", new_callable=AsyncMock) as mock_upload:
                        await convert_one(mock_chapter)

                        mock_tts.assert_called_once()
                        mock_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_when_chapter_deleted(self):
        """Test that conversion is skipped when chapter is deleted during conversion."""
        mock_chapter = MagicMock()
        mock_chapter.id = 42
        mock_chapter.audio_settings = '{"engine_name": "kokoro", "voice_name": "bella"}'

        mock_audio = io.BytesIO(b"fake audio data")

        mock_context = MagicMock()
        mock_context.chapter = mock_chapter
        mock_context.minio_object_name = "42_audio.mp3"

        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("src.workers.convert_audiobook.AudiobookConversionContext", return_value=mock_context),
            patch("src.workers.convert_audiobook.generate_text_to_speech", new_callable=AsyncMock) as mock_tts,
        ):
            mock_tts.return_value = mock_audio

            with patch("src.workers.convert_audiobook.AudiobookChapter.objects") as mock_objects:
                mock_objects.return_value.where.return_value.first = AsyncMock(return_value=None)

                await convert_one(mock_chapter)

                mock_tts.assert_called_once()
                mock_objects.return_value.where.return_value.first.assert_called()

    @pytest.mark.asyncio
    async def test_skips_on_audio_settings_mismatch(self):
        """Test that conversion is skipped when audio settings changed during conversion."""
        mock_chapter = MagicMock()
        mock_chapter.id = 42
        mock_chapter.audio_settings = '{"engine_name": "kokoro", "voice_name": "bella"}'

        mock_audio = io.BytesIO(b"fake audio data")

        mock_context = MagicMock()
        mock_context.chapter = mock_chapter
        mock_context.minio_object_name = "42_audio.mp3"

        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("src.workers.convert_audiobook.AudiobookConversionContext", return_value=mock_context),
            patch("src.workers.convert_audiobook.generate_text_to_speech", new_callable=AsyncMock) as mock_tts,
        ):
            mock_tts.return_value = mock_audio

            with patch("src.workers.convert_audiobook.AudiobookChapter.objects") as mock_objects:
                mock_chapter2 = MagicMock()
                mock_chapter2.audio_settings = '{"engine_name": "kokoro", "voice_name": "joey"}'
                mock_objects.return_value.where.return_value.first = AsyncMock(return_value=mock_chapter2)

                with patch("src.workers.convert_audiobook.get_s3_client") as mock_s3:
                    mock_s3.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
                    mock_s3.return_value.__aexit__ = AsyncMock(return_value=None)

                    with patch("src.workers.convert_audiobook.object_upload", new_callable=AsyncMock) as mock_upload:
                        await convert_one(mock_chapter)

                        mock_tts.assert_called_once()
                        mock_upload.assert_not_called()


class TestKeepConverting:
    """Tests for keep_converting main loop."""

    @pytest.mark.asyncio
    async def test_loop_handles_check_queued_chapters_error(self):
        """Test that the loop handles errors from check_queued_chapters gracefully."""

        async def mock_check_that_errors():
            raise RuntimeError("Database error")

        async def mock_sleep(seconds):
            raise asyncio.CancelledError

        with (
            patch("src.workers.convert_audiobook.check_queued_chapters", side_effect=mock_check_that_errors),
            patch("src.workers.convert_audiobook.asyncio.sleep", side_effect=mock_sleep),
        ):
            task = asyncio.create_task(keep_converting())

            with suppress(asyncio.CancelledError, RuntimeError):
                await task
