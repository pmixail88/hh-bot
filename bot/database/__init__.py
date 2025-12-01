from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from core.config import get_config

def create_async_sessionmaker():
    config = get_config()
    
    engine = create_async_engine(
        config.database.url,
        echo=getattr(config.database, 'echo', False),
        pool_pre_ping=True
    )
    
    return async_sessionmaker(engine, expire_on_commit=False)

# Экспортируем модели и репозитории
from .models import User, SearchFilter, Vacancy, UserVacancy, LLMSettings
from .repository import (
    UserRepository, 
    SearchFilterRepository, 
    VacancyRepository,
    UserVacancyRepository,
    LLMSettingsRepository
)

__all__ = [
    'create_async_sessionmaker',
    'User', 'SearchFilter', 'Vacancy', 'UserVacancy', 'LLMSettings',
    'UserRepository', 'SearchFilterRepository', 'VacancyRepository',
    'UserVacancyRepository', 'LLMSettingsRepository'
]