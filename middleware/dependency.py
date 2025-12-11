from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import DependencyProvider
from utils.logger import get_logger  # Добавить

logger = get_logger(__name__)  # Добавить

class DependencyMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        async with self.session_pool() as session:
            provider = DependencyProvider(data['bot'], session)
            data['provider'] = provider
            
            try:
                # Логируем входящие события
                if isinstance(event, Message):
                    logger.debug(f"📨 Сообщение от {event.from_user.id}: {event.text}")
                elif isinstance(event, CallbackQuery):
                    logger.debug(f"🖱️ Callback от {event.from_user.id}: {event.data}")
                    
                return await handler(event, data)
            except Exception as e:
                logger.error(f"❌ Ошибка в middleware: {e}", exc_info=True)
                raise