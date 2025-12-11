from typing import AsyncGenerator
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from services.simple_cache import SimpleCache

from database.repository import UserRepository, SearchFilterRepository, VacancyRepository, LLMSettingsRepository, UserVacancyRepository
from services.hh_service import HHService
from services.llm_service import LLMService
from services.cache import CacheService
from core.config import get_config

class DependencyProvider:
    def __init__(self, bot: Bot, session: AsyncSession):
        self.bot = bot
        self.session = session
        self.config = get_config()
        
        # Инициализируем репозитории
        self._user_repo = UserRepository(session)
        self._search_filter_repo = SearchFilterRepository(session)
        self._vacancy_repo = VacancyRepository(session)
        self._llm_settings_repo = LLMSettingsRepository(session)
        self._user_vacancy_repo = UserVacancyRepository(session)
        
        # Инициализируем сервисы
        self._hh_service = HHService(self.config.hh)
        self._llm_service = LLMService(self.config.llm)
        #self._cache_service = CacheService(self.config.redis.url)
        self._cache_service = SimpleCache()
    
    @property
    def user_repo(self) -> UserRepository:
        return self._user_repo
    
    @property
    def search_filter_repo(self) -> SearchFilterRepository:
        return self._search_filter_repo
    
    @property
    def vacancy_repo(self) -> VacancyRepository:
        return self._vacancy_repo
    
    @property
    def llm_settings_repo(self) -> LLMSettingsRepository:
        return self._llm_settings_repo
    
    @property
    def user_vacancy_repo(self) -> UserVacancyRepository:
        return self._user_vacancy_repo
    
    @property
    def hh_service(self) -> HHService:
        return self._hh_service
    
    @property
    def llm_service(self) -> LLMService:
        return self._llm_service
    
    @property
    def cache_service(self) -> CacheService:
        return self._cache_service