from typing import AsyncGenerator
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from services.secure_config import SecureConfigService
from services.simple_cache import SimpleCache
from services.secure_storage import SecureStorageService
from database.repository import CoverLetterRepository, GeneratedResumeRepository, UserRepository, SearchFilterRepository, VacancyRepository, LLMSettingsRepository, UserVacancyRepository
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
        self._generated_resume_repo = GeneratedResumeRepository(session)
        self._cover_letter_repo = CoverLetterRepository(session)
        
        # Инициализируем сервисы
        self._hh_service = HHService(self.config.hh)
        self._llm_service = LLMService(self.config.llm)
        self._cache_service = CacheService(self.config.redis.url) #SimpleCache() - стоял
        
        # Добавляем сервис безопасного хранения
        # Исправлено: правильные имена параметров
        self._secure_storage = SecureStorageService(user_repo=self._user_repo, llm_settings_repo=self._llm_settings_repo)  # Исправлено: llm_settings_repo вместо llm_settings_repository
        
        # Добавляем SecureConfigService
        self._secure_config = SecureConfigService(self._secure_storage)
        
        
    
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
    
    @property
    def generated_resume_repo(self) -> GeneratedResumeRepository:
        return self._generated_resume_repo
    
    @property
    def cover_letter_repo(self) -> CoverLetterRepository:
        return self._cover_letter_repo
    
    @property
    def secure_storage(self) -> SecureStorageService:
        """Получить сервис безопасного хранения"""
        return self._secure_storage
    
    @property
    def secure_config(self) -> SecureConfigService:
        """Получить сервис конфигурации"""
        return self._secure_config