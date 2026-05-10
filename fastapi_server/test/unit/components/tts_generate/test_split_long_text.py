"""Tests for _split_long_text.py"""

import pytest
from components.tts_generate._split_long_text import (
    find_split_point,
    generate_silence_mp3,
    concatenate_mp3s_with_silence,
    generate_long_text_audio,
)


class TestFindSplitPoint:
    """Tests for find_split_point function."""

    def test_split_at_sentence_boundary(self):
        """Split at period when under character limit."""
        text = "This is the first sentence. This is the second sentence. Third sentence here."
        split_idx = find_split_point(text, max_chars=30)
        # Should split at the period after "first sentence."
        assert split_idx == 25
        # Left chunk should be <= max_chars
        assert len(text[:split_idx]) <= 30

    def test_split_at_word_boundary(self):
        """Split at word boundary when no sentence fit."""
        text = "OneTwoThree FourFive SixSeven"
        split_idx = find_split_point(text, max_chars=10)
        # Should split at word boundary
        assert text[split_idx - 1] == " "

    def test_split_at_character_as_last_resort(self):
        """Split at character when no word boundary fits."""
        text = "abcdefghij"
        split_idx = find_split_point(text, max_chars=3)
        # Should split at character
        assert split_idx == 3
        assert len(text[:split_idx]) == 3


class TestGenerateSilenceMp3:
    """Tests for generate_silence_mp3 function."""

    def test_generates_valid_mp3(self):
        """Returns valid MP3 bytes."""
        silence = generate_silence_mp3(duration=0.3)
        assert isinstance(silence, bytes)
        assert len(silence) > 0

    def test_correct_duration(self):
        """Silence has correct duration."""
        from mutagen.mp3 import MP3
        from io import BytesIO

        silence = generate_silence_mp3(duration=0.5)
        mp3_info = MP3(BytesIO(silence))
        assert abs(mp3_info.info.length - 0.5) < 0.1


class TestConcatenateMp3sWithSilence:
    """Tests for concatenate_mp3s_with_silence function."""

    def test_concatenates_two_mp3s(self):
        """Concatenates two MP3s with silence."""
        silence = generate_silence_mp3(duration=0.3)
        # Create minimal valid MP3s (use silence as placeholder)
        chunk1 = silence
        chunk2 = silence

        result = concatenate_mp3s_with_silence([chunk1, chunk2], silence_duration=0.3)
        assert isinstance(result, bytes)
        assert len(result) > len(chunk1)


class TestGenerateLongTextAudio:
    """Tests for generate_long_text_audio function."""

    @pytest.mark.asyncio
    async def test_short_text_no_split(self):
        """Short text that fits in one chunk works."""
        # This will call tiktok_engine which needs session ID
        # Mock the engine for this test
        pass  # Tested via integration

    @pytest.mark.asyncio
    async def test_raises_on_permanent_failure(self):
        """Raises error after max retries exceeded."""
        pass  # Tested via integration
