import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.config import get_config
from database.models import Base
from sqlalchemy.ext.asyncio import create_async_engine

async def manual_migration():
    config = get_config()
    
    print("🔄 Выполняем миграцию вручную...")
    
    engine = create_async_engine(config.database.url, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Создаем все таблицы заново
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Миграция выполнена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(manual_migration())