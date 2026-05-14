import pytest
from fastapi import HTTPException

from routes.audiobook import validate_audiobook_engine
from schemas.audiobook import QueueChapterRequest


def test_rejects_kokoro_engine():
    """Test that kokoro engine is rejected."""
    settings = QueueChapterRequest(value="kokoro_en-US-amy")
    with pytest.raises(HTTPException) as exc_info:
        validate_audiobook_engine(settings)
    assert exc_info.value.status_code == 400
    assert "kokoro" in exc_info.value.detail.lower()


def test_rejects_kitten_engine():
    """Test that kitten engine is rejected."""
    settings = QueueChapterRequest(value="kitten_en-US-amy")
    with pytest.raises(HTTPException) as exc_info:
        validate_audiobook_engine(settings)
    assert exc_info.value.status_code == 400
    assert "kitten" in exc_info.value.detail.lower()


def test_accepts_edge_engine():
    """Test that edge engine is accepted."""
    settings = QueueChapterRequest(value="edge_en-US-JennyNeural")
    # Should not raise
    validate_audiobook_engine(settings)


def test_accepts_tiktok_engine():
    """Test that tiktok engine is accepted."""
    settings = QueueChapterRequest(value="tiktok_en-US-JennyNeural")
    # Should not raise
    validate_audiobook_engine(settings)
