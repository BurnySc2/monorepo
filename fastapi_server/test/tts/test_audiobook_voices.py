import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_audiobook_voices_filters_engines():
    """Test that /voices-audiobook only returns tiktok and edge voices."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/tts-generate/voices-audiobook")
        assert response.status_code == 200
        voices = response.json()
        engine_types = {v["engine"] for v in voices}
        assert engine_types == {"tiktok", "edge"}
        # Verify kokoro and kitten are NOT included
        assert "kokoro" not in engine_types
        assert "kitten" not in engine_types
