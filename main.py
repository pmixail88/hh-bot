import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import get_config
from handlers import router
from database import create_async_sessionmaker
from middleware.dependency import DependencyMiddleware
from middleware.error_handler import ErrorHandlerMiddleware
from utils.logger import setup_colored_logger, logger  # Импортируем новый логгер
from utils.scheduler import VacancyScheduler
#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)

async def main():
    # Настраиваем логгер
    logger.info("🚀 Начинаю запуск бота...")
    
    config = get_config()
    
    # Логируем базовую информацию
    logger.info(f"Конфигурация загружена: {'DEBUG' if config.bot.debug else 'PRODUCTION'} режим")
    logger.info(f"База данных: {config.database.host}")
    
    bot = Bot(token=config.bot.token)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Создаем пул сессий
    session_pool = create_async_sessionmaker()
    
    # Регистрируем middleware
    dp.update.middleware(DependencyMiddleware(session_pool))
    dp.update.middleware(ErrorHandlerMiddleware())
    
    # Регистрируем роутеры
    dp.include_router(router)
    
    logger.info("✅ Все роутеры и middleware зарегистрированы")
    logger.info("🤖 Бот запущен и готов к работе!")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал прерывания, останавливаю бота...")
    except Exception as e:
        logger.critical(f"💥 Критическая ошибка в работе бота: {e}", exc_info=True)
    finally:
        logger.info("👋 Завершение работы бота")

if __name__ == "__main__":
    asyncio.run(main())