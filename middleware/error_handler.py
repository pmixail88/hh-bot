from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from utils.logger import get_logger
logger = get_logger(__name__)

class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            # Игнорируем распространенные ошибки Telegram
            error_message = str(e)
            if "message is not modified" in error_message:
                return None
            if "message to edit not found" in error_message:
                return None
            if "query is too old" in error_message:
                return None
                
            logger.error(f"❌ Необработанная ошибка: {e}", exc_info=True)
            
            # Отправляем сообщение об ошибке пользователю
            try:
                if isinstance(event, Message):
                    await event.answer(
                        "❌ Произошла ошибка при обработке запроса. Попробуйте позже.",
                        parse_mode="HTML"
                    )
                elif isinstance(event, CallbackQuery):
                    await event.answer(
                        "❌ Произошла ошибка. Попробуйте позже.",
                        show_alert=True
                    )
            except Exception:
                pass
            
            return None