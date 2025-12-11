# database/update_database.py
import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в путь Python
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy import inspect

def update_database():
    """Обновить структуру базы данных"""
    try:
        # Импортируем здесь, после добавления пути
        from database import get_db_url
        from models import User, Base
        
        print("Подключаемся к базе данных...")
        engine = create_engine(get_db_url())
        
        # Создаем таблицы, если их нет
        print("Создаем таблицы...")
        Base.metadata.create_all(engine)
        
        # Проверяем существующие колонки
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('users')]
        
        print(f"Существующие колонки: {existing_columns}")
        
        # Список необходимых колонок для шифрования
        encryption_columns = [
            'hh_client_id_encrypted', 'hh_client_secret_encrypted',
            'hh_access_token_encrypted', 'hh_refresh_token_encrypted',
            'llm_api_key_encrypted', 'llm_base_url_encrypted',
            'contact_email_encrypted', 'contact_phone_encrypted'
        ]
        
        # Список необходимых колонок для данных
        data_columns = [
            'hh_client_id', 'hh_client_secret', 'hh_access_token',
            'hh_refresh_token', 'llm_api_key', 'llm_base_url',
            'contact_email', 'contact_phone'
        ]
        
        # Список колонок для шифрования
        key_columns = [
            'encryption_key', 'encryption_salt', 'data_integrity_hash'
        ]
        
        # Создаем недостающие колонки
        with engine.connect() as conn:
            # Проверяем и добавляем колонки для данных
            for column in data_columns:
                if column not in existing_columns:
                    print(f"Добавляем колонку: {column}")
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column} TEXT"))
            
            # Проверяем и добавляем колонки для шифрования
            for column in encryption_columns:
                if column not in existing_columns:
                    print(f"Добавляем колонку: {column}")
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column} TEXT"))
            
            # Проверяем и добавляем колонки для ключей
            for column in key_columns:
                if column not in existing_columns:
                    print(f"Добавляем колонку: {column}")
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {column} TEXT"))
            
            conn.commit()
        
        print("✅ База данных успешно обновлена!")
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении базы данных: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_database()