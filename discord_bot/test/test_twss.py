from unittest.mock import AsyncMock, Mock, patch

import pytest
from postgrest import APIResponse, AsyncSelectRequestBuilder#pyre-fixme[21]

from commands.public_twss import public_twss


@pytest.mark.asyncio
async def test_public_twss():
    fake_bot = Mock()
    fake_event = Mock()
    fake_event.guild_id = 123
    fake_event.author_id = 456
    fake_event.author.username = 'some_username'
    message = '--days 5'
    data = [{'who': 'burny', 'when': '2022-01-02', 'what': 'some_quote', 'emoji_name': 'twss', 'guild_id': 123}]

    with patch.object(AsyncSelectRequestBuilder, 'execute', AsyncMock()) as execute:
        execute.return_value = APIResponse(data=data)
        result = await public_twss(fake_bot, fake_event, message)

    assert isinstance(result, str)
    assert result == "2022-01-02 burny: some_quote"
