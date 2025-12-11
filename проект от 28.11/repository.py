from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update, func
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .models import User, SearchFilter, Vacancy, UserVacancy, LLMSettings

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_or_create_user(self, telegram_id: str, full_name: str, username: str = None) -> User:
        """Получить или создать пользователя"""
        user = await self.get_user_by_telegram_id(telegram_id)
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                full_name=full_name,
                username=username
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            
            # Создаем настройки по умолчанию
            llm_settings = LLMSettings(user_id=user.id)
            self.session.add(llm_settings)
            
            # Создаем фильтр по умолчанию
            default_filter = SearchFilter(
                user_id=user.id,
                name="Основной",
                region="Санкт-Петербург"
            )
            self.session.add(default_filter)
            
            await self.session.commit()
        
        return user
    
    async def update_user_profile(self, telegram_id: str, **kwargs) -> Optional[User]:
        """Обновить профиль пользователя"""
        user = await self.get_user_by_telegram_id(telegram_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            await self.session.commit()
        return user
    
    async def get_all_active_users(self) -> List[User]:
        """Получить всех активных пользователей"""
        result = await self.session.execute(
            select(User).where(User.scheduler_enabled == True)
        )
        return result.scalars().all()
    
    async def update_user_scheduler_settings(self, telegram_id: str, scheduler_enabled: bool = None, 
                                           scheduler_times: str = None, check_interval_hours: int = None) -> Optional[User]:
        """Обновить настройки планировщика пользователя"""
        user = await self.get_user_by_telegram_id(telegram_id)
        if user:
            if scheduler_enabled is not None:
                user.scheduler_enabled = scheduler_enabled
            if scheduler_times is not None:
                user.scheduler_times = scheduler_times
            if check_interval_hours is not None:
                user.check_interval_hours = check_interval_hours
            user.updated_at = datetime.utcnow()
            await self.session.commit()
        return user

class SearchFilterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_filters(self, user_id: int) -> List[SearchFilter]:
        """Получить все фильтры пользователя"""
        result = await self.session.execute(
            select(SearchFilter).where(SearchFilter.user_id == user_id)
        )
        return result.scalars().all()
    
    async def get_active_filter(self, user_id: int) -> Optional[SearchFilter]:
        """Получить активный фильтр пользователя"""
        result = await self.session.execute(
            select(SearchFilter).where(
                and_(
                    SearchFilter.user_id == user_id,
                    SearchFilter.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def update_filter(self, filter_id: int, **kwargs) -> Optional[SearchFilter]:
        """Обновить параметры фильтра"""
        result = await self.session.execute(
            select(SearchFilter).where(SearchFilter.id == filter_id)
        )
        filter_obj = result.scalar_one_or_none()
        
        if filter_obj:
            for key, value in kwargs.items():
                if hasattr(filter_obj, key):
                    setattr(filter_obj, key, value)
            filter_obj.updated_at = datetime.utcnow()
            await self.session.commit()
        
        return filter_obj
    
    async def create_filter(self, user_id: int, name: str, **kwargs) -> SearchFilter:
        """Создать новый фильтр"""
        # Деактивируем другие фильтры пользователя
        await self.session.execute(
            update(SearchFilter)
            .where(SearchFilter.user_id == user_id)
            .values(is_active=False)
        )
        
        filter_obj = SearchFilter(
            user_id=user_id,
            name=name,
            is_active=True,
            **kwargs
        )
        self.session.add(filter_obj)
        await self.session.commit()
        await self.session.refresh(filter_obj)
        return filter_obj
    
    async def set_active_filter(self, user_id: int, filter_id: int) -> bool:
        """Установить активный фильтр"""
        # Деактивируем все фильтры пользователя
        await self.session.execute(
            update(SearchFilter)
            .where(SearchFilter.user_id == user_id)
            .values(is_active=False)
        )
        
        # Активируем выбранный фильтр
        result = await self.session.execute(
            update(SearchFilter)
            .where(
                and_(
                    SearchFilter.id == filter_id,
                    SearchFilter.user_id == user_id
                )
            )
            .values(is_active=True)
        )
        await self.session.commit()
        return result.rowcount > 0

class VacancyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_vacancy_by_hh_id(self, hh_id: str) -> Optional[Vacancy]:
        """Найти вакансию по HH ID"""
        result = await self.session.execute(
            select(Vacancy).where(Vacancy.hh_id == hh_id)
        )
        return result.scalar_one_or_none()
    
    async def create_vacancy(self, vacancy_data: Dict[str, Any]) -> Vacancy:
        """Создать новую вакансию"""
        vacancy = Vacancy(**vacancy_data)
        self.session.add(vacancy)
        await self.session.commit()
        await self.session.refresh(vacancy)
        return vacancy
    
    async def get_or_create_vacancy(self, vacancy_data: Dict[str, Any]) -> Vacancy:
        """Получить или создать вакансию"""
        existing = await self.get_vacancy_by_hh_id(vacancy_data['hh_id'])
        if existing:
            return existing
        return await self.create_vacancy(vacancy_data)
    
    async def get_recent_vacancies(self, hours: int = 24) -> List[Vacancy]:
        """Получить вакансии за последние N часов"""
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.session.execute(
            select(Vacancy).where(
                and_(
                    Vacancy.published_at >= time_threshold,
                    Vacancy.is_archived == False
                )
            ).order_by(Vacancy.published_at.desc())
        )
        return result.scalars().all()
    
    async def get_vacancies_by_filters(self, search_filter: SearchFilter, limit: int = 50) -> List[Vacancy]:
        """Получить вакансии по фильтрам из БД"""
        query = select(Vacancy).where(Vacancy.is_archived == False)
        
        # Применяем фильтры
        if search_filter.region:
            query = query.where(Vacancy.area_name.ilike(f"%{search_filter.region}%"))
        
        if search_filter.keywords:
            keywords = search_filter.keywords.split()
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append(Vacancy.name.ilike(f"%{keyword}%"))
                keyword_conditions.append(Vacancy.description.ilike(f"%{keyword}%"))
            query = query.where(or_(*keyword_conditions))
        
        if search_filter.salary_from:
            query = query.where(
                or_(
                    Vacancy.salary_from >= search_filter.salary_from,
                    Vacancy.salary_to >= search_filter.salary_from
                )
            )
        
        # Период публикации
        if search_filter.period:
            time_threshold = datetime.utcnow() - timedelta(days=search_filter.period)
            query = query.where(Vacancy.published_at >= time_threshold)
        
        query = query.order_by(Vacancy.published_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def archive_old_vacancies(self, days: int = 30):
        """Архивировать старые вакансии"""
        time_threshold = datetime.utcnow() - timedelta(days=days)
        
        await self.session.execute(
            update(Vacancy).where(
                and_(
                    Vacancy.published_at < time_threshold,
                    Vacancy.is_archived == False
                )
            ).values(is_archived=True)
        )
        await self.session.commit()
    
    async def check_and_archive_vacancies(self, hh_service) -> int:
        """Проверить и архивировать вакансии через HH API"""
        # Получаем неархивированные вакансии
        result = await self.session.execute(
            select(Vacancy).where(Vacancy.is_archived == False)
        )
        vacancies = result.scalars().all()
        
        archived_count = 0
        for vacancy in vacancies:
            try:
                is_archived = await hh_service.check_vacancy_archived(vacancy.hh_id)
                if is_archived:
                    vacancy.is_archived = True
                    archived_count += 1
            except Exception as e:
                # Логируем ошибку, но продолжаем обработку
                continue
        
        if archived_count > 0:
            await self.session.commit()
        
        return archived_count

class UserVacancyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

        async def get_user_vacancies(self, user_id: int) -> List[UserVacancy]:
            """Получить все вакансии пользователя с предзагрузкой вакансий"""
            result = await self.session.execute(
                select(UserVacancy)
                .options(joinedload(UserVacancy.vacancy))  # Предзагружаем связанные вакансии
                .where(UserVacancy.user_id == user_id)
                .order_by(UserVacancy.created_at.desc())
            )
            return result.scalars().all()
        '''
        async def get_user_vacancies(self, user_id: int) -> List[UserVacancy]:
            """Получить все вакансии пользователя"""
            result = await self.session.execute(
                select(UserVacancy)
                .where(UserVacancy.user_id == user_id)
                .order_by(UserVacancy.created_at.desc())
            )
            return result.scalars().all()
    
        async def get_user_vacancies(self, user_id: int) -> List[UserVacancy]:
            """Получить все вакансии пользователя с предзагрузкой вакансий"""
            result = await self.session.execute(
                select(UserVacancy)
                .options(joinedload(UserVacancy.vacancy))
                .where(UserVacancy.user_id == user_id)
                .order_by(UserVacancy.created_at.desc())
            )
            return result.scalars().all()
    '''

    '''
    async def get_user_vacancies_with_vacancies(self, user_id: int) -> List[UserVacancy]:
        """Получить все вакансии пользователя с предзагрузкой и фильтрацией"""
        result = await self.session.execute(
            select(UserVacancy)
            .options(joinedload(UserVacancy.vacancy))
            .where(
                and_(
                    UserVacancy.user_id == user_id,
                    Vacancy.is_archived == False  # Добавляем фильтр здесь
                )
            )
            .join(Vacancy)  # Обязательно JOIN для фильтрации
            .order_by(UserVacancy.created_at.desc())
        )
        return result.scalars().all()
    '''
    
    async def get_user_vacancy(self, user_id: int, vacancy_id: int) -> Optional[UserVacancy]:
        """Получить конкретную связь пользователь-вакансия"""
        result = await self.session.execute(
            select(UserVacancy).where(
                and_(
                    UserVacancy.user_id == user_id,
                    UserVacancy.vacancy_id == vacancy_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def create_user_vacancy(self, user_id: int, vacancy_id: int, **kwargs) -> UserVacancy:
        """Создать связь пользователь-вакансия"""
        user_vacancy = UserVacancy(
            user_id=user_id,
            vacancy_id=vacancy_id,
            **kwargs
        )
        self.session.add(user_vacancy)
        await self.session.commit()
        await self.session.refresh(user_vacancy)
        return user_vacancy
    
    async def update_user_vacancy(self, user_vacancy_id: int, **kwargs) -> Optional[UserVacancy]:
        """Обновить связь пользователь-вакансия"""
        result = await self.session.execute(
            select(UserVacancy).where(UserVacancy.id == user_vacancy_id)
        )
        user_vacancy = result.scalar_one_or_none()
        
        if user_vacancy:
            for key, value in kwargs.items():
                if hasattr(user_vacancy, key):
                    setattr(user_vacancy, key, value)
            user_vacancy.updated_at = datetime.utcnow()
            await self.session.commit()
        
        return user_vacancy
    
    async def get_favorite_vacancies(self, user_id: int) -> List[UserVacancy]:
        """Получить избранные вакансии пользователя"""
        result = await self.session.execute(
            select(UserVacancy)
            .where(
                and_(
                    UserVacancy.user_id == user_id,
                    UserVacancy.is_favorite == True
                )
            )
            .order_by(UserVacancy.updated_at.desc())
        )
        return result.scalars().all()
    
    async def get_applied_vacancies(self, user_id: int) -> List[UserVacancy]:
        """Получить вакансии, на которые откликнулся пользователь"""
        result = await self.session.execute(
            select(UserVacancy)
            .where(
                and_(
                    UserVacancy.user_id == user_id,
                    UserVacancy.is_applied == True
                )
            )
            .order_by(UserVacancy.updated_at.desc())
        )
        return result.scalars().all()
    
    async def get_unviewed_vacancies(self, user_id: int) -> List[UserVacancy]:
        """Получить непросмотренные вакансии пользователя"""
        result = await self.session.execute(
            select(UserVacancy)
            .where(
                and_(
                    UserVacancy.user_id == user_id,
                    UserVacancy.is_viewed == False
                )
            )
            .order_by(UserVacancy.created_at.desc())
        )
        return result.scalars().all()
    
    async def mark_as_viewed(self, user_vacancy_id: int) -> bool:
        """Пометить вакансию как просмотренную"""
        result = await self.session.execute(
            update(UserVacancy)
            .where(UserVacancy.id == user_vacancy_id)
            .values(is_viewed=True, viewed_at=datetime.utcnow())
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_vacancy_stats(self, user_id: int) -> Dict[str, int]:
        """Получить статистику по вакансиям пользователя"""
        total = await self.session.execute(
            select(func.count(UserVacancy.id))
            .where(UserVacancy.user_id == user_id)
        )
        total_count = total.scalar()
        
        favorites = await self.session.execute(
            select(func.count(UserVacancy.id))
            .where(
                and_(
                    UserVacancy.user_id == user_id,
                    UserVacancy.is_favorite == True
                )
            )
        )
        favorites_count = favorites.scalar()
        
        applied = await self.session.execute(
            select(func.count(UserVacancy.id))
            .where(
                and_(
                    UserVacancy.user_id == user_id,
                    UserVacancy.is_applied == True
                )
            )
        )
        applied_count = applied.scalar()
        
        unviewed = await self.session.execute(
            select(func.count(UserVacancy.id))
            .where(
                and_(
                    UserVacancy.user_id == user_id,
                    UserVacancy.is_viewed == False
                )
            )
        )
        unviewed_count = unviewed.scalar()
        
        return {
            'total': total_count or 0,
            'favorites': favorites_count or 0,
            'applied': applied_count or 0,
            'unviewed': unviewed_count or 0
        }

class LLMSettingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_user_id(self, user_id: int) -> Optional[LLMSettings]:
        """Получить настройки LLM по ID пользователя"""
        result = await self.session.execute(
            select(LLMSettings).where(LLMSettings.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_settings(self, settings_id: int, **kwargs) -> Optional[LLMSettings]:
        """Обновить настройки LLM"""
        result = await self.session.execute(
            select(LLMSettings).where(LLMSettings.id == settings_id)
        )
        settings = result.scalar_one_or_none()
        
        if settings:
            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            settings.updated_at = datetime.utcnow()
            await self.session.commit()
        
        return settings
    
    async def create_default_settings(self, user_id: int) -> LLMSettings:
        """Создать настройки по умолчанию для пользователя"""
        settings = LLMSettings(user_id=user_id)
        self.session.add(settings)
        await self.session.commit()
        await self.session.refresh(settings)
        return settings
    
    async def get_llm_settings_dict(self, user_id: int) -> Dict[str, Any]:
        """Получить настройки LLM в виде словаря для сервиса"""
        settings = await self.get_by_user_id(user_id)
        if not settings:
            return {}
        
        return {
            'api_key': settings.api_key,
            'base_url': settings.base_url,
            'model_name': settings.model_name,
            'temperature': settings.temperature,
            'max_tokens': settings.max_tokens
        }

class StatisticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Получить общую статистику пользователя"""
        # Статистика по вакансиям
        vacancy_stats = await UserVacancyRepository(self.session).get_vacancy_stats(user_id)
        
        # Количество фильтров
        filters_count = await self.session.execute(
            select(func.count(SearchFilter.id))
            .where(SearchFilter.user_id == user_id)
        )
        filters_count = filters_count.scalar() or 0
        
        # Дата регистрации
        user_result = await self.session.execute(
            select(User.created_at)
            .where(User.id == user_id)
        )
        registration_date = user_result.scalar()
        
        return {
            'vacancies': vacancy_stats,
            'filters_count': filters_count,
            'registration_date': registration_date,
            'days_registered': (datetime.utcnow() - registration_date).days if registration_date else 0
        }
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Получить системную статистику"""
        # Общее количество пользователей
        total_users = await self.session.execute(select(func.count(User.id)))
        total_users = total_users.scalar() or 0
        
        # Активные пользователи
        active_users = await self.session.execute(
            select(func.count(User.id))
            .where(User.scheduler_enabled == True)
        )
        active_users = active_users.scalar() or 0
        
        # Общее количество вакансий
        total_vacancies = await self.session.execute(select(func.count(Vacancy.id)))
        total_vacancies = total_vacancies.scalar() or 0
        
        # Неархивированные вакансии
        active_vacancies = await self.session.execute(
            select(func.count(Vacancy.id))
            .where(Vacancy.is_archived == False)
        )
        active_vacancies = active_vacancies.scalar() or 0
        
        # Вакансии за последние 24 часа
        recent_vacancies = await self.session.execute(
            select(func.count(Vacancy.id))
            .where(
                and_(
                    Vacancy.published_at >= datetime.utcnow() - timedelta(hours=24),
                    Vacancy.is_archived == False
                )
            )
        )
        recent_vacancies = recent_vacancies.scalar() or 0
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_vacancies': total_vacancies,
            'active_vacancies': active_vacancies,
            'recent_vacancies': recent_vacancies
        }