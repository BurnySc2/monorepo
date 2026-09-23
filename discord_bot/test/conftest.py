"""Test isolation for handler imports.

TECH DEBT stopgap until lazy factory (Option 1): patches
``hikari.GatewayBot`` to return a MagicMock so importing
``handlers.messages`` -> ``bot`` -> ``create_bot`` does not raise
``ValueError`` for ``DISCORD_KEY=test_key``. Runs at import time because
``conftest`` loads before test collection. Keeps real ``Remind`` binding
via ``Remind(mock_bot)`` so ``COMMAND_MAP`` alias checks still hold.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

_mock_bot = MagicMock(name="gateway_bot")
_gateway_patcher = patch("hikari.GatewayBot", return_value=_mock_bot)
_gateway_patcher.start()
