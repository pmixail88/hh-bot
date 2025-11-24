import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.config import get_settings
from bot.handlers import (
    start_router,
    search_settings_router,
    vacancies_router,
    profile_router,
    llm_settings_router
)
from bot.utils.scheduler import VacancyScheduler
import sys
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def main():
    # Получаем настройки
    settings = get_settings()
    
    # Инициализируем базу данных
    from bot.db.init_db import init_database
    init_database()
    
    # Создаем бота
    bot = Bot(token=settings.bot_token)
    
    # Создаем диспетчер
    dp = Dispatcher()
    
    # Регистрируем роутеры
    dp.include_router(start_router)
    dp.include_router(search_settings_router)
    dp.include_router(vacancies_router)
    dp.include_router(profile_router)
    dp.include_router(llm_settings_router)
    
    # Создаем и запускаем планировщик
    scheduler = VacancyScheduler(bot)
    scheduler.start()
    
    logger.info("Бот запускается...")
    
    try:
        # Запускаем бота
        await dp.start_polling(bot)
    finally:
        # Останавливаем планировщик при завершении
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())