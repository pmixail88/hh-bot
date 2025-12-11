import pytest
from aiogram.types import Message, User, Chat
from unittest.mock import AsyncMock

from handlers.base import cmd_start

class TestHandlers:
    @pytest.mark.asyncio
    async def test_start_command(self):
        message = Message(
            message_id=1,
            date=None,
            chat=Chat(id=1, type="private"),
            from_user=User(id=1, is_bot=False, first_name="Test"),
            text="/start"
        )
        
        provider = AsyncMock()
        provider.user_repo.get_or_create_user = AsyncMock()
        provider.user_repo.get_user_by_telegram_id = AsyncMock(return_value=None)
        
        state = AsyncMock()
        
        await cmd_start(message, provider, state)
        
        provider.user_repo.get_or_create_user.assert_called_once()