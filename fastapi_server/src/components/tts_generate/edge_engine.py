"""
Edge TTS - Microsoft free cloud TTS, 74+ languages, 322 voices.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass

import edge_tts


@dataclass
class VoiceInfo:
    """Information about a voice."""
    name: str
    short_name: str
    gender: str
    locale: str


VOICES = [
    VoiceInfo("en-US-AriaNeural", "Aria", "Female", "en-US"),
    VoiceInfo("en-US-GuyNeural", "Guy", "Male", "en-US"),
    VoiceInfo("en-US-JennyNeural", "Jenny", "Female", "en-US"),
    VoiceInfo("en-GB-SoniaNeural", "Sonia", "Female", "en-GB"),
    VoiceInfo("en-GB-RyanNeural", "Ryan", "Male", "en-GB"),
    VoiceInfo("de-DE-KatjaNeural", "Katja", "Female", "de-DE"),
    VoiceInfo("de-DE-ConradNeural", "Conrad", "Male", "de-DE"),
    VoiceInfo("fr-FR-DeniseNeural", "Denise", "Female", "fr-FR"),
    VoiceInfo("fr-FR-HenriNeural", "Henri", "Male", "fr-FR"),
    VoiceInfo("es-ES-ElviraNeural", "Elvira", "Female", "es-ES"),
    VoiceInfo("es-MX-DaliaNeural", "Dalia", "Female", "es-MX"),
    VoiceInfo("ja-JP-NanamiNeural", "Nanami", "Female", "ja-JP"),
    VoiceInfo("ja-JP-KeitaNeural", "Keita", "Male", "ja-JP"),
    VoiceInfo("ko-KR-SunHiNeural", "SunHi", "Female", "ko-KR"),
    VoiceInfo("zh-CN-XiaoxiaoNeural", "Xiaoxiao", "Female", "zh-CN"),
    VoiceInfo("zh-CN-YunxiNeural", "Yunxi", "Male", "zh-CN"),
    VoiceInfo("pt-BR-FranciscaNeural", "Francisca", "Female", "pt-BR"),
    VoiceInfo("pt-BR-AntonioNeural", "Antonio", "Male", "pt-BR"),
    VoiceInfo("it-IT-ElsaNeural", "Elsa", "Female", "it-IT"),
    VoiceInfo("it-IT-DiegoNeural", "Diego", "Male", "it-IT"),
]


async def list_voices_async() -> list[VoiceInfo]:
    """List all available Edge TTS voices."""
    return VOICES


async def generate_audio_async(
    voice: str,
    text: str,
    output_path: str | None = None,
) -> tuple[str, float]:
    """
    Generate audio using Edge TTS.

    Args:
        voice: Voice name (e.g., "en-US-AriaNeural")
        text: Text to synthesize
        output_path: Optional output path. If None, a temp file is created.

    Returns:
        Tuple of (output_path, duration_seconds)
    """
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".mp3")

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

    # Calculate duration based on text length (approximate: ~10 chars/second)
    duration = max(0.1, len(text) / 10.0)

    return output_path, duration
