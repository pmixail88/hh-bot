import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.config import get_config
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_tables_structure():
    config = get_config()
    
    engine = create_async_engine(config.database.url, echo=False)
    
    try:
        async with engine.connect() as conn:
            # Получаем список всех таблиц
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.scalars().all()
            
            print("📊 Структура таблиц в базе данных:")
            print("=" * 50)
            
            for table in tables:
                print(f"\n🛠️ Таблица: {table}")
                print("-" * 30)
                
                # Получаем колонки для каждой таблицы
                columns_result = await conn.execute(text(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = '{table}'
                    ORDER BY ordinal_position
                """))
                
                columns = columns_result.fetchall()
                for col in columns:
                    nullable = "NULL" if col.is_nullable == 'YES' else "NOT NULL"
                    default = f"DEFAULT {col.column_default}" if col.column_default else ""
                    print(f"  {col.column_name} ({col.data_type}) {nullable} {default}")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_tables_structure())