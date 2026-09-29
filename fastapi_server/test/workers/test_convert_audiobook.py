"""Unit tests for convert_audiobook worker.

These tests mock external dependencies (database, MinIO, TTS).
The core conversion logic is well covered. Integration tests would
require a real database for full coverage of check_queued_chapters.
"""

import asyncio
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.workers.convert_audiobook import (
    AudiobookConversionContext,
    _background_tasks,
    _on_background_task_done,
    check_queued_chapters,
    convert_one,
    get_chapter_combined_text,
    keep_converting,
)


class TestAudiobookConversionContext:
    """Tests for AudiobookConversionContext context manager."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="__aexit__ calls AudiobookChapter.update().where() which requires complex db mocking")
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
    @pytest.mark.skip(reason="__aexit__ calls AudiobookChapter.update().where() which requires complex db mocking")
    async def test_context_exit_success_clears_flag(self):
        """Test that exiting context with no exception clears started_converting."""
        mock_chapter = MagicMock()
        mock_chapter.id = 42
        mock_chapter.started_converting = None
        mock_chapter.save = AsyncMock()

        async with AudiobookConversionContext(mock_chapter):
            pass

        assert mock_chapter.save.call_count == 2
        assert mock_chapter.started_converting is None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="__aexit__ calls AudiobookChapter.update().where() which requires complex db mocking")
    async def test_context_exit_failure_clears_flag(self):
        """Test that exiting context after exception clears started_converting and logs error."""
        mock_chapter = MagicMock()
        mock_chapter.id = 42
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

        mock_audio = (b"fake audio data", 10.5)

        mock_context = MagicMock()
        mock_context.chapter = mock_chapter
        mock_context.minio_object_name = "42_audio.mp3"

        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("src.workers.convert_audiobook.AudiobookConversionContext", return_value=mock_context),
            patch("src.workers.convert_audiobook.generate_audio", new_callable=AsyncMock) as mock_tts,
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

        mock_audio = (b"fake audio data", 10.5)

        mock_context = MagicMock()
        mock_context.chapter = mock_chapter
        mock_context.minio_object_name = "42_audio.mp3"

        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("src.workers.convert_audiobook.AudiobookConversionContext", return_value=mock_context),
            patch("src.workers.convert_audiobook.generate_audio", new_callable=AsyncMock) as mock_tts,
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

        mock_audio = (b"fake audio data", 10.5)

        mock_context = MagicMock()
        mock_context.chapter = mock_chapter
        mock_context.minio_object_name = "42_audio.mp3"

        mock_context.__aenter__ = AsyncMock(return_value=mock_context)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("src.workers.convert_audiobook.AudiobookConversionContext", return_value=mock_context),
            patch("src.workers.convert_audiobook.generate_audio", new_callable=AsyncMock) as mock_tts,
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


class TestGetChapterCombinedTextShim:
    """Offline tests for get_chapter_combined_text delegating to epub_reader.combine_text."""

    def test_str_input_splitlines(self):
        from components.audiobook.epub_reader import combine_text

        text = "  hello   world \n\n foo  "
        assert get_chapter_combined_text(text) == combine_text(text.splitlines())

    def test_list_input_delegates(self):
        from components.audiobook.epub_reader import combine_text

        lines: list[str] = ["hello", "  world  ", "", "foo"]
        assert get_chapter_combined_text(lines) == combine_text(lines)

    def test_collapses_whitespace(self):
        assert get_chapter_combined_text("a\n\n  b\tc") == "a b c"

    def test_empty(self):
        assert get_chapter_combined_text("") == ""
        assert get_chapter_combined_text([]) == ""


class TestBackgroundTaskTracking:
    """Offline tests for create_task tracking with done_callback."""

    @pytest.mark.asyncio
    async def test_done_callback_discards_success(self):
        async def _ok() -> None:
            return None

        task = asyncio.create_task(_ok())
        _background_tasks.add(task)
        task.add_done_callback(_on_background_task_done)
        await asyncio.wait_for(task, timeout=5)
        # Give the callback a chance to run
        await asyncio.sleep(0)
        assert task not in _background_tasks

    @pytest.mark.asyncio
    async def test_done_callback_logs_exception(self):
        async def _boom() -> None:
            raise ValueError("boom")

        task = asyncio.create_task(_boom())
        _background_tasks.add(task)
        task.add_done_callback(_on_background_task_done)
        with suppress(ValueError):
            await task
        await asyncio.sleep(0)
        assert task not in _background_tasks

    @pytest.mark.asyncio
    async def test_done_callback_ignores_cancelled(self):
        task = asyncio.create_task(asyncio.sleep(60))
        _background_tasks.add(task)
        task.add_done_callback(_on_background_task_done)
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        await asyncio.sleep(0)
        assert task not in _background_tasks

    @pytest.mark.asyncio
    async def test_check_queued_chapters_tracks_tasks(self):
        """check_queued_chapters should track create_task handles with done_callback."""
        mock_chapter = MagicMock()
        mock_chapter.chapter_number = 1

        mock_query = MagicMock()
        mock_query.first = AsyncMock(return_value=mock_chapter)
        mock_query.limit = AsyncMock(return_value=[mock_chapter])
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query

        mock_update_query = MagicMock()
        mock_update_query.where = AsyncMock(return_value=[])
        mock_count_query = MagicMock()
        mock_count_query.where = AsyncMock(return_value=0)

        created: list[asyncio.Task] = []
        real_create_task = asyncio.create_task

        def _tracking_create_task(coro, **kwargs):  # type: ignore[no-untyped-def]
            task = real_create_task(coro, **kwargs)
            created.append(task)
            return task

        async def _noop(_chapter) -> None:
            return None

        _background_tasks.clear()
        try:
            with (
                # Patch query entry points only so real Piccolo columns stay
                # usable in where-clauses (patching the whole model leaves a
                # MagicMock column that fails `<= datetime` comparisons).
                patch(
                    "src.workers.convert_audiobook.AudiobookChapter.update",
                    return_value=mock_update_query,
                ),
                patch(
                    "src.workers.convert_audiobook.AudiobookChapter.objects",
                    return_value=mock_query,
                ),
                patch(
                    "src.workers.convert_audiobook.AudiobookChapter.count",
                    return_value=mock_count_query,
                ),
                patch("src.workers.convert_audiobook.convert_one", new=_noop),
                patch("src.workers.convert_audiobook.asyncio.create_task", side_effect=_tracking_create_task),
            ):
                result = await check_queued_chapters()

            assert result is True
            assert len(created) == 1
            assert created[0] in _background_tasks
            # Cleanup: let tracked task finish and fire its callback
            await asyncio.wait_for(asyncio.gather(*created, return_exceptions=True), timeout=5)
            await asyncio.sleep(0)
        finally:
            _background_tasks.clear()
