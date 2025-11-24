from bot.db.database import engine, Base
from bot.db.models import User, SearchFilter, Vacancy, UserVacancy, LLMSettings, GeneratedDocument
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

def init_database():
    """
    Инициализация базы данных - создание всех таблиц
    """
    print("Инициализация базы данных...")
    try:
        # Подключаемся к базе данных и создаем таблицы в одной транзакции
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                # Создаем все таблицы
                Base.metadata.create_all(bind=conn)
                trans.commit()
                print("База данных инициализирована успешно!")
                logger.info("Database tables created successfully")
            except Exception as e:
                trans.rollback()
                raise e
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        logger.error(f"Database initialization error: {e}")
        raise e


if __name__ == "__main__":
    init_database()