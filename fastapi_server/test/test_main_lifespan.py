"""Gate3 critical tests for NLTK lazy fix: lifespan resilience.

Lifespan must boot even when NLTK data is unavailable (LookupError/OSError
from _ensure_nltk_data), but must not swallow unexpected errors (ValueError
propagates, proving no blind catch).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

import main


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [LookupError("missing punkt_tab"), OSError("disk unavailable")])
async def test_lifespan_continues_when_nltk_data_unavailable(monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
    """Lifespan yields/boots when _ensure_nltk_data raises LookupError/OSError."""
    monkeypatch.setattr(main, "initialize_rustfs", AsyncMock(return_value=None))
    mock_ensure = MagicMock(side_effect=error)
    monkeypatch.setattr(main, "ensure_nltk_data", mock_ensure)

    async with main.lifespan(MagicMock()):
        pass

    assert mock_ensure.call_count == 1


@pytest.mark.asyncio
async def test_lifespan_propagates_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lifespan does not swallow unexpected errors like ValueError."""
    monkeypatch.setattr(main, "initialize_rustfs", AsyncMock(return_value=None))
    mock_ensure = MagicMock(side_effect=ValueError("unexpected"))
    monkeypatch.setattr(main, "ensure_nltk_data", mock_ensure)

    with pytest.raises(ValueError, match="unexpected"):
        async with main.lifespan(MagicMock()):
            pass

    assert mock_ensure.call_count == 1
