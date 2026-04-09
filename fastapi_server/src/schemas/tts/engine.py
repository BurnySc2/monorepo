from __future__ import annotations

from typing import Literal

TTSEngine = Literal["edge", "kokoro", "kitten", "pocket", "tiktok"]

ENGINES: list[TTSEngine] = ["edge", "kokoro", "kitten", "pocket", "tiktok"]

__all__ = ["TTSEngine", "ENGINES"]
