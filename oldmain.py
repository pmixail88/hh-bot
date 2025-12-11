import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.db.init_db import init_database
from bot.handlers.start_handler import router as start_router
from bot.handlers.search_settings_handler import router as search_settings_router
from bot.handlers.search_settings_states import router as search_states_router
from bot.utils.logger import setup_colored_logger

logger = setup_colored_logger(__name__)

async def main():
    try:
        settings = get_settings()
        init_database()
        
        bot = Bot(token=settings.bot_token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        dp.include_router(start_router)
        dp.include_router(search_settings_router)
        dp.include_router(search_states_router)
        
        logger.info("Бот запускается...")
        logger.info(f"Bot ID: {settings.bot_token.split(':')[0]}")
        
        logger.info("Запуск polling бота...")
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске бота: {e}", exc_info=True)
    finally:
        logger.info("Бот завершил работу")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Приложение завершено")
    except Exception as e:
        logger.error(f"Необработанное исключение: {e}", exc_info=True)