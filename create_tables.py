from bot.db.database import engine
from bot.db.models import User, SearchFilter, Vacancy, UserVacancy, LLMSettings, GeneratedDocument
from sqlalchemy import text

def create_tables_explicitly():
    print("Создание таблиц...")
    
    # Подключаемся к базе данных
    with engine.connect() as conn:
        # Начинаем транзакцию
        trans = conn.begin()
        try:
            # Проверяем существующие таблицы
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            existing_tables = [row[0] for row in result]
            print(f"Существующие таблицы до создания: {existing_tables}")
            
            # Создаем таблицы
            User.__table__.create(bind=conn, checkfirst=True)
            SearchFilter.__table__.create(bind=conn, checkfirst=True)
            Vacancy.__table__.create(bind=conn, checkfirst=True)
            UserVacancy.__table__.create(bind=conn, checkfirst=True)
            LLMSettings.__table__.create(bind=conn, checkfirst=True)
            GeneratedDocument.__table__.create(bind=conn, checkfirst=True)
            
            # Подтверждаем транзакцию
            trans.commit()
            
            # Проверяем созданные таблицы
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            new_tables = [row[0] for row in result]
            print(f"Существующие таблицы после создания: {new_tables}")
            
            print("Таблицы успешно созданы!")
            
        except Exception as e:
            print(f"Ошибка при создании таблиц: {e}")
            trans.rollback()
            raise

if __name__ == "__main__":
    create_tables_explicitly()