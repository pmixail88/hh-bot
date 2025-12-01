import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_postgres():
    """Тестирование подключения к PostgreSQL"""
    
    # Ваш текущий URL - ЗАМЕНИТЕ на реальные данные
    database_url = "postgresql+asyncpg://neondb_owner:npg_X2MjE8RsNdDH@ep-solitary-brook-agmztrhf-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    
    try:
        print(f"🔧 Подключаемся к PostgreSQL: {database_url}")
        
        # Создаем асинхронный engine
        engine = create_async_engine(database_url, echo=True)
        
        # Тестируем подключение
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Подключение успешно! PostgreSQL версия: {version}")
        
        # Закрываем соединение
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        print("\n💡 Возможные проблемы:")
        print("1. PostgreSQL не запущен")
        print("2. Неправильный username/password")
        print("3. База данных 'hh_bot' не существует")
        print("4. Проблемы с правами доступа")
        print("\n🛠️  Решения:")
        print("• Запустите PostgreSQL: sudo systemctl start postgresql")
        print("• Создайте базу: CREATE DATABASE hh_bot;")
        print("• Проверьте логин/пароль")
        print("• Или используйте SQLite для тестирования")

if __name__ == "__main__":
    asyncio.run(test_postgres())