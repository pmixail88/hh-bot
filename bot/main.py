import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import get_config
from handlers import router
from database import create_async_sessionmaker
from middleware.dependency import DependencyMiddleware
from middleware.error_handler import ErrorHandlerMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    config = get_config()
    
    bot = Bot(token=config.bot.token)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Создаем пул сессий
    session_pool = create_async_sessionmaker()
    
    # Регистрируем middleware
    dp.update.middleware(DependencyMiddleware(session_pool))
    dp.update.middleware(ErrorHandlerMiddleware())
    
    # Регистрируем роутеры
    dp.include_router(router)
    
    logger.info("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())