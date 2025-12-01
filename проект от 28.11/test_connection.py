import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.config import get_config
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_connection():
    config = get_config()
    
    print(f"🔗 Тестируем подключение к: {config.database.url}")
    
    engine = create_async_engine(
        config.database.url,
        echo=True
    )
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"✅ Подключение успешно! PostgreSQL версия: {version}")
            
            # Проверяем существующие таблицы
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = result.scalars().all()
            print(f"📊 Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"   - {table}")
                
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())