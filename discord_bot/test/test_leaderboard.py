from unittest.mock import AsyncMock, Mock, patch

import pytest
from postgrest import APIResponse, AsyncSelectRequestBuilder#pyre-fixme[21]

from commands.public_leaderboard import public_leaderboard


@pytest.mark.asyncio
async def test_public_leaderboard():
    fake_bot = Mock()
    fake_event = Mock()
    fake_guild_member = Mock()
    fake_guild_member.id = 456
    fake_guild_member.display_name = "test_user_name"
    fake_bot.rest.fetch_members = AsyncMock()
    fake_bot.rest.fetch_members.return_value = [fake_guild_member]
    message = ''
    data = [{'guild_id': 123, 'author_id': 456, 'count': 123456789}]

    with patch.object(AsyncSelectRequestBuilder, 'execute', AsyncMock()) as execute:
        execute.return_value = APIResponse(data=data)
        result = await public_leaderboard(fake_bot, fake_event, message)

    assert isinstance(result, str)
    assert "GLOBAL LEADERBOARD" in result
    assert "test_user_name" in result
    assert "123456789" in result
