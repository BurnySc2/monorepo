from __future__ import annotations

from typing import Literal

TTSEngine = Literal["edge", "kokoro", "kitten", "tiktok"]

ENGINES: list[TTSEngine] = ["edge", "kokoro", "kitten", "tiktok"]

__all__ = ["TTSEngine", "ENGINES"]
