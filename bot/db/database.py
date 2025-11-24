from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from bot.config import get_settings

# Получаем настройки
settings = get_settings()

# Создаем engine с дополнительными параметрами для Neon
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Проверяет соединение перед использованием
    echo=True  # Для отладки - можно убрать позже
)

# Создаем сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()


# Функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()