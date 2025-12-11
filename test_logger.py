# test_logger.py
#!/usr/bin/env python3
"""
Тестирование нового логгера
"""

import asyncio
from utils.logger import setup_colored_logger, logger

def test_sync_logging():
    """Синхронное тестирование"""
    print("=" * 50)
    print("🧪 ТЕСТИРОВАНИЕ СИНХРОННОГО ЛОГИРОВАНИЯ")
    print("=" * 50)
    
    logger.debug("Debug сообщение - видно только в файле")
    logger.info("✅ Info сообщение - зеленое в консоли")
    logger.warning("⚠️ Warning сообщение - желтое в консоли")
    logger.error("❌ Error сообщение - красное в консоли")
    logger.critical("💥 Critical сообщение - красный фон в консоли")
    
    print("\n" + "=" * 50)
    print("📁 Логи записаны в:")
    print("   - logs/YYYY-MM-DD.log (все сообщения)")
    print("   - logs/YYYY-MM-DD_errors.log (только ERROR и CRITICAL)")
    print("=" * 50)

async def test_async_logging():
    """Асинхронное тестирование"""
    print("\n🧪 Тестирование асинхронного логирования...")
    
    # Имитация асинхронной операции
    import random
    
    for i in range(5):
        await asyncio.sleep(0.1)
        level = random.choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        message = f"Асинхронное сообщение #{i+1} (уровень: {level})"
        
        if level == 'DEBUG':
            logger.debug(message)
        elif level == 'INFO':
            logger.info(message)
        elif level == 'WARNING':
            logger.warning(message)
        elif level == 'ERROR':
            logger.error(message)

async def main():
    test_sync_logging()
    await test_async_logging()
    
    # Проверка именованных логгеров
    print("\n🧪 Тестирование именованных логгеров...")
    
    # Разные модули
    from utils.logger import get_logger
    
    hh_logger = get_logger('hh_service')
    hh_logger.info("HH Service: Тестовое сообщение")
    
    db_logger = get_logger('database')
    db_logger.info("Database: Тестовое сообщение")
    
    bot_logger = get_logger('bot')
    bot_logger.info("Bot: Тестовое сообщение")

if __name__ == "__main__":
    asyncio.run(main())