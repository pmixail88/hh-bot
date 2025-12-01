import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.config import get_config
from database.models import Base
from sqlalchemy.ext.asyncio import create_async_engine

async def create_tables():
    config = get_config()
    
    print(f"🔗 Подключаемся к базе: {config.database.url}")
    
    engine = create_async_engine(
        config.database.url,
        echo=True
    )
    
    try:
        async with engine.begin() as conn:
            print("🗑️ Удаляем существующие таблицы...")
            await conn.run_sync(Base.metadata.drop_all)
            print("📦 Создаем новые таблицы...")
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Таблицы успешно созданы в Neon PostgreSQL!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())