from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import DependencyProvider

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
                return await handler(event, data)
            except Exception as e:
                # Логируем ошибку
                from bot.utils.logger import setup_colored_logger
                logger = setup_colored_logger(__name__)
                logger.error(f"❌ Ошибка в middleware: {e}")
                raise