"""
Common utilities for TTS engines.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import httpx


def download_file(url: str, target: Path) -> None:
    """Download file to a temp dir, then move to target on completion."""
    if target.exists():
        return
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / target.name
        with httpx.Client() as client:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
            with tmp_path.open("wb") as f:
                f.write(response.content)
        shutil.move(tmp_path, target)
