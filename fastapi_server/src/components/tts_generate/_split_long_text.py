"""
TikTok Long Text Helper - Split long text into chunks for TikTok TTS.

Handles text that's too long for a single TikTok TTS request by:
1. Auto-discovering the character limit through trial/error
2. Splitting text at natural boundaries (sentences → words → chars) using NLTK
3. Generating audio for each chunk
4. Concatenating with silence between chunks
"""

from __future__ import annotations

import io
from typing import Protocol

import nltk  # noqa: I001
from loguru import logger
from pydub import AudioSegment


class TikTokGenerator(Protocol):
    """Protocol for TikTok TTS generate function."""

    async def __call__(self, voice: str, text: str) -> tuple[bytes, float]:
        """Generate audio for text. Returns (audio_bytes, duration)."""
        ...


# Default character limit to try first (will auto-reduce if this fails)
DEFAULT_MAX_CHARS = 2000
# Minimum chunk size to prevent infinite recursion
MIN_CHUNK_SIZE = 50
# Maximum recursion depth for limit discovery
MAX_AUTO_RETRY_DEPTH = 5


def find_split_point(text: str, max_chars: int) -> int:
    """
    Find the best position to split text within max_chars limit.

    Uses NLTK for natural sentence splitting when possible.

    Split priority:
    1. NLTK sentence boundary
    2. Sentence boundary (., ?, !)
    3. Word boundary (space)
    4. Character boundary (any position)

    Args:
        text: Text to split
        max_chars: Maximum characters allowed

    Returns:
        Index where to split (1 to len(text) - 1)
    """
    if len(text) <= max_chars:
        return len(text)

    # Try NLTK sentence tokenization first
    try:
        sentences = nltk.sent_tokenize(text)
        if len(sentences) > 1:
            # Find the last sentence that fits within max_chars
            cumulative = 0
            for sent in sentences:
                if cumulative + len(sent) <= max_chars:
                    cumulative += len(sent)
                else:
                    if cumulative > 0:
                        return cumulative
                    break
    except (LookupError, Exception):  # noqa: BLE001
        # Fall back to manual splitting, but surface that NLTK was unavailable.
        logger.warning("NLTK sentence tokenizer unavailable; falling back to manual splitting", exc_info=True)

    # Try sentence boundary with punctuation + space
    for punct in (". ", "? ", "! "):
        idx = text.rfind(punct, 0, max_chars)
        if idx > 0:
            return idx + 1  # Include the punctuation

    # Try earlier sentence boundary
    for punct in (".", "?", "!"):
        idx = text.rfind(punct, 0, max_chars)
        if idx > 0:
            return idx + 1

    # Try word boundary
    idx = text.rfind(" ", 0, max_chars)
    if idx > 0:
        return idx

    # Last resort: split at max_chars
    return min(max_chars, len(text))


def split_text_recursive(text: str, max_chars: int) -> list[str]:
    """
    Recursively split text into chunks that fit within max_chars.

    Args:
        text: Text to split
        max_chars: Maximum characters per chunk

    Returns:
        List of text chunks
    """
    if len(text) <= max_chars:
        return [text]

    split_idx = find_split_point(text, max_chars)
    left_chunk = text[:split_idx]
    right_chunk = text[split_idx:]

    # Ensure neither chunk is empty
    if not left_chunk:
        left_chunk = text[: max_chars // 2]
        right_chunk = text[len(left_chunk) :]

    if not right_chunk:
        return [left_chunk]

    # Recursively split both halves
    left_chunks = split_text_recursive(left_chunk, max_chars)
    right_chunks = split_text_recursive(right_chunk, max_chars)

    return left_chunks + right_chunks


def generate_silence_mp3(duration: float, sample_rate: int = 24000) -> bytes:
    """
    Generate silent MP3 audio.

    Args:
        duration: Silence duration in seconds
        sample_rate: Audio sample rate (TikTok uses 24000)

    Returns:
        MP3 bytes
    """
    # Generate silent audio segment using pydub (produces valid MP3)
    silence = AudioSegment.silent(duration=int(duration * 1000), frame_rate=sample_rate)

    # Export to MP3 bytes
    mp3_buffer = io.BytesIO()
    silence.export(mp3_buffer, format="mp3")
    return mp3_buffer.getvalue()


def concatenate_mp3s_with_silence(
    mp3_chunks: list[bytes],
    silence_duration: float = 0.3,
) -> bytes:
    """
    Concatenate multiple MP3s with silence between them.

    Args:
        mp3_chunks: List of MP3 byte chunks
        silence_duration: Duration of silence between chunks

    Returns:
        Combined MP3 bytes
    """
    if not mp3_chunks:
        return b""

    if len(mp3_chunks) == 1:
        return mp3_chunks[0]

    silence = generate_silence_mp3(silence_duration)

    # Concatenate: chunk1 + silence + chunk2 + ...
    result = io.BytesIO()
    for i, chunk in enumerate(mp3_chunks):
        result.write(chunk)
        if i < len(mp3_chunks) - 1:
            result.write(silence)

    return result.getvalue()


async def generate_long_text_audio(
    voice: str,
    text: str,
    tiktok_generate: TikTokGenerator,
    silence_between_seconds: float = 0.3,
    initial_max_chars: int | None = None,
) -> tuple[bytes, float]:
    """
    Generate audio for long text by chunking and concatenating.

    Args:
        voice: TikTok voice code
        text: Text to synthesize
        tiktok_generate: Function to call TikTok TTS (voice, text) -> (audio_bytes, duration)
        silence_between_seconds: Silence duration between chunks
        initial_max_chars: Initial max chars to try (None = auto DEFAULT_MAX_CHARS)

    Returns:
        Tuple of (combined_audio_bytes, total_duration_seconds)

    Raises:
        RuntimeError: If text cannot be synthesized after max retries
    """
    if not text:
        return b"", 0.0

    if initial_max_chars is None:
        initial_max_chars = DEFAULT_MAX_CHARS

    max_chars = initial_max_chars

    # Try different chunk sizes until one works
    for attempt in range(MAX_AUTO_RETRY_DEPTH):
        try:
            chunks = split_text_recursive(text, max_chars)
            logger.info(f"Trying with max_chars={max_chars}, got {len(chunks)} chunks")

            # Generate audio for each chunk
            mp3_chunks: list[bytes] = []
            total_duration = 0.0

            for chunk_text in chunks:
                if not chunk_text.strip():
                    continue
                audio_bytes, duration = await tiktok_generate(voice, chunk_text)
                mp3_chunks.append(audio_bytes)
                total_duration += duration

            # Concatenate with silence
            combined = concatenate_mp3s_with_silence(
                mp3_chunks,
                silence_duration=silence_between_seconds,
            )

            # Add silence duration to total
            if len(mp3_chunks) > 1:
                total_duration += silence_between_seconds * (len(mp3_chunks) - 1)

            return combined, total_duration

        except RuntimeError as e:
            error_msg = str(e)
            if "Text too long" in error_msg or "status_code" in error_msg:
                # Reduce chunk size and retry
                max_chars = max_chars // 2
                if max_chars < MIN_CHUNK_SIZE:
                    raise RuntimeError(
                        f"Cannot synthesize text even with very small chunks (min {MIN_CHUNK_SIZE} chars): {e}"
                    ) from e
                logger.warning(f"Text too long, retrying with max_chars={max_chars}")
                continue
            raise

    raise RuntimeError(f"Failed after {MAX_AUTO_RETRY_DEPTH} attempts")


# Export for convenience
__all__ = [
    "find_split_point",
    "split_text_recursive",
    "generate_silence_mp3",
    "concatenate_mp3s_with_silence",
    "generate_long_text_audio",
    "DEFAULT_MAX_CHARS",
    "MIN_CHUNK_SIZE",
    "MAX_AUTO_RETRY_DEPTH",
]
