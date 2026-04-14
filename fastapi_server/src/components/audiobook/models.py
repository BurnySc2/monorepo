from __future__ import annotations

import re


def normalize_title(title: str) -> str:
    normalized_title = title.title()
    normalized_title = re.sub(r"[^\w]", " ", normalized_title)
    normalized_title = re.sub(r" +", " ", normalized_title)
    return normalized_title.strip()


def normalize_filename(text: str) -> str:
    return re.sub(" ", "_", normalize_title(text))


def get_chapter_combined_text(text: str) -> str:
    combined = " ".join(row for row in text)
    return re.sub(r"\s+", " ", combined)
