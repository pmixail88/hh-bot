import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import List
import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import SchedulerConfig
from utils.lazy_imports import HHService
from database.models import User, SearchFilter
from database.repository import UserRepository, VacancyRepository, SearchFilterRepository

logger = logging.getLogger(__name__)

class VacancyScheduler:
    def __init__(self, bot: Bot, session: AsyncSession, config: SchedulerConfig):
        self.bot = bot
        self.session = session
        self.config = config
        
        # ИСПРАВЛЕНИЕ: Получаем HHConfig из глобального конфига
        from core.config import get_config
        hh_config = get_config().hh
        
        self.hh_service = HHService(hh_config)  # Передаем правильный конфиг
        self.scheduler = AsyncIOScheduler()
        
        # Инициализируем репозитории
        self.user_repo = UserRepository(session)
        self.vacancy_repo = VacancyRepository(session)
        self.filter_repo = SearchFilterRepository(session)

    def start(self):
        """Запуск планировщика"""
        if not self.config.enabled:
            logger.info("⏰ Планировщик отключен в настройках")
            return

        # Парсим время проверок по умолчанию
        default_times = self.config.default_times.split(',')
        
        for time_str in default_times:
            try:
                hour, minute = map(int, time_str.strip().split(':'))
                self.scheduler.add_job(
                    self.check_all_users_vacancies,
                    CronTrigger(hour=hour, minute=minute, timezone='Europe/Moscow'),
                    id=f'daily_check_{time_str}',
                    replace_existing=True
                )
                logger.info(f"⏰ Добавлена задача на {time_str}")
            except ValueError as e:
                logger.error(f"❌ Ошибка парсинга времени {time_str}: {e}")

        self.scheduler.start()
        logger.info("✅ Планировщик запущен")

    async def check_all_users_vacancies(self):
        """Проверка вакансий для всех пользователей"""
        logger.info("🔍 Запуск проверки вакансий для всех пользователей...")
        
        # Получаем активных пользователей
        users = await self._get_all_active_users()
        if not users:
            logger.info("ℹ️ Нет активных пользователей для проверки")
            return

        for user in users:
            try:
                await self.check_user_vacancies(user)
                await asyncio.sleep(1)  # Задержка между пользователями
            except Exception as e:
                logger.error(f"❌ Ошибка при проверке пользователя {user.id}: {e}")

    async def _get_all_active_users(self) -> List[User]:
        """Получить всех активных пользователей"""
        result = await self.session.execute(
            select(User).where(User.scheduler_enabled == True)
        )
        return result.scalars().all()

    async def check_user_vacancies(self, user: User):
        """Проверка вакансий для конкретного пользователя"""
        try:
            filters = await self.filter_repo.get_user_filters(user.id)
            if not filters:
                return

            for search_filter in filters:
                if not search_filter.is_active:
                    continue

                # Проверяем, нужно ли делать проверку по интервалу
                if search_filter.last_checked:
                    time_since_last_check = datetime.utcnow() - search_filter.last_checked
                    if time_since_last_check.total_seconds() < user.check_interval_hours * 3600:
                        continue

                # Ищем вакансии
                vacancies = await self.hh_service.search_vacancies(search_filter)
                new_vacancies = []

                for vacancy_data in vacancies:
                    # Проверяем, есть ли уже такая вакансия
                    existing = await self.vacancy_repo.get_vacancy_by_hh_id(vacancy_data['hh_id'])
                    if not existing:
                        vacancy = await self.vacancy_repo.create_vacancy(vacancy_data)
                        new_vacancies.append(vacancy)

                # Отправляем уведомление о новых вакансиях
                if new_vacancies:
                    await self.send_vacancies_notification(user, new_vacancies)

                # Обновляем время последней проверки
                await self.filter_repo.update_filter(
                    search_filter.id, 
                    last_checked=datetime.utcnow()
                )

        except Exception as e:
            logger.error(f"❌ Ошибка при проверке вакансий пользователя {user.id}: {e}")

    async def send_vacancies_notification(self, user: User, vacancies: List):
        """Отправка уведомления о новых вакансиях"""
        try:
            message_text = (
                f"🎯 <b>Найдены новые вакансии по вашему запросу</b>\n\n"
                f"Количество: {len(vacancies)}\n\n"
                f"Для просмотра используйте команду /menu или нажмите кнопку ниже:"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💼 Посмотреть вакансии", callback_data="menu_vacancies")]
            ])
            
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            logger.info(f"📤 Отправлено уведомление пользователю {user.telegram_id} о {len(vacancies)} вакансиях")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления пользователю {user.telegram_id}: {e}")

    def stop(self):
        """Остановка планировщика"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Планировщик остановлен")