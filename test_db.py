import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def test_database():
    """Тестирование подключения к базе данных"""
    
    # Используем SQLite для тестирования
    database_url = "sqlite+aiosqlite:///./test_hh_bot.db"
    
    try:
        print(f"🔧 Подключаемся к базе: {database_url}")
        
        # Создаем асинхронный engine
        engine = create_async_engine(database_url, echo=True)
        
        # Тестируем подключение
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            print("✅ Подключение к базе данных успешно!")
        
        # Закрываем соединение
        await engine.dispose()
        print("✅ Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        print("\n💡 Рекомендации:")
        print("1. Убедитесь, что DATABASE_URL в .env файле использует асинхронный драйвер")
        print("2. Для PostgreSQL используйте: postgresql+asyncpg://...")
        print("3. Для SQLite используйте: postgresql+asyncpg:///...")
        print("4. Установите драйвер: pip install asyncpg (для PostgreSQL) или pip install aiosqlite (для SQLite)")

if __name__ == "__main__":
    asyncio.run(test_database())