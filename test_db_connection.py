import asyncio
from sqlalchemy import create_engine, text
from bot.config import get_settings

def test_db_connection():
    print("Тестирование подключения к базе данных...")
    
    settings = get_settings()
    print(f"DATABASE_URL: {settings.database_url}")
    
    # Создаем engine
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        echo=True
    )
    
    try:
        # Проверяем подключение
        with engine.connect() as conn:
            # Выполняем простой запрос
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"Подключение успешно: {row.test == 1}")
            
            # Проверим информацию о базе данных
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"Версия PostgreSQL: {version[0]}")
            
            # Проверим текущую схему
            result = conn.execute(text("SELECT current_schema()"))
            schema = result.fetchone()
            print(f"Текущая схема: {schema[0]}")
            
        print("Подключение к базе данных работает корректно!")
        
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_connection()