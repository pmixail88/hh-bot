from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
from bot.services.hh_service import HHService
from bot.db.database import get_db
from bot.db.models import User, SearchFilter, Vacancy, UserVacancy
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List
from aiogram import Bot
from bot.config import get_settings


class VacancyScheduler:
    """
    Класс для планирования регулярной проверки новых вакансий
    """
    def __init__(self, bot: Bot):
        self.scheduler = AsyncIOScheduler()
        self.hh_service = HHService()
        self.bot = bot

    def start(self):
        """
        Запуск планировщика
        Добавляем задачу на ежедневную проверку вакансий в 9:00 утра
        """
        self.scheduler.add_job(
            self.check_new_vacancies,
            CronTrigger(hour=9, minute=0),  # Ежедневно в 9:00
            id='check_vacancies_job',
            name='Проверка новых вакансий',
            replace_existing=True
        )
        
        self.scheduler.start()
        print("Планировщик запущен. Задача на проверку вакансий добавлена.")

    def stop(self):
        """
        Остановка планировщика
        """
        self.scheduler.shutdown()

    async def check_new_vacancies(self):
        """
        Проверка новых вакансий для всех пользователей с активными фильтрами
        """
        print(f"Запуск проверки новых вакансий: {datetime.now()}")
        
        db: Session = next(get_db())
        
        try:
            # Получаем всех пользователей с активными фильтрами
            active_users = db.query(User).join(SearchFilter).filter(
                User.is_active == True,
                SearchFilter.is_active == True
            ).distinct().all()
            
            new_vacancies_for_users = {}  # Словарь для хранения новых вакансий для каждого пользователя
            
            for user in active_users:
                # Получаем фильтры пользователя
                user_filters = db.query(SearchFilter).filter(
                    SearchFilter.user_id == user.id,
                    SearchFilter.is_active == True
                ).all()
                
                for user_filter in user_filters:
                    # Поиск вакансий по фильтрам пользователя
                    vacancies = self.hh_service.search_vacancies(
                        text=user_filter.position,
                        city=user_filter.city,
                        salary=user_filter.min_salary,
                        employment=user_filter.employment_types.split(',') if user_filter.employment_types else None,
                        experience=user_filter.experience_level,
                        period=user_filter.freshness_days,
                        employer_type='direct' if user_filter.only_direct_employers else None,
                        company_size=user_filter.company_size if user_filter.company_size else None
                    )
                    
                    # Обрабатываем найденные вакансии
                    for vacancy_data in vacancies:
                        # Проверяем, существует ли уже такая вакансия в базе
                        existing_vacancy = db.query(Vacancy).filter(Vacancy.hh_id == vacancy_data['id']).first()
                        
                        if not existing_vacancy:
                            # Создаем новую вакансию
                            new_vacancy = Vacancy(
                                hh_id=vacancy_data['id'],
                                title=vacancy_data['title'],
                                company=vacancy_data['company'],
                                city=vacancy_data['city'],
                                salary_from=vacancy_data['salary_from'],
                                salary_to=vacancy_data['salary_to'],
                                salary_currency=vacancy_data['salary_currency'],
                                description=vacancy_data['description'],
                                url=vacancy_data['url'],
                                published_at=vacancy_data['published_at'],
                                employer_id=vacancy_data['employer_id']
                            )
                            
                            db.add(new_vacancy)
                            db.flush() # Чтобы получить ID новой вакансии
                            
                            # Создаем связь с пользователем
                            user_vacancy = UserVacancy(
                                user_id=user.id,
                                vacancy_id=new_vacancy.id,
                                is_interesting=True
                            )
                            
                            db.add(user_vacancy)
                            
                            # Добавляем вакансию в список новых для отправки пользователю
                            if user.id not in new_vacancies_for_users:
                                new_vacancies_for_users[user.id] = []
                            new_vacancies_for_users[user.id].append({
                                'vacancy': new_vacancy,
                                'user_filter': user_filter
                            })
                        else:
                            # Проверяем, есть ли уже связь с этим пользователем
                            existing_user_vacancy = db.query(UserVacancy).filter(
                                UserVacancy.user_id == user.id,
                                UserVacancy.vacancy_id == existing_vacancy.id
                            ).first()
                            
                            if not existing_user_vacancy:
                                # Создаем связь с пользователем
                                user_vacancy = UserVacancy(
                                    user_id=user.id,
                                    vacancy_id=existing_vacancy.id,
                                    is_interesting=True
                                )
                                
                                db.add(user_vacancy)
            
            db.commit()
            
            # Отправляем новые вакансии пользователям
            await self.send_new_vacancies_to_users(new_vacancies_for_users)
            
            print(f"Проверка вакансий завершена: {datetime.now()}")
            
        except Exception as e:
            print(f"Ошибка при проверке вакансий: {e}")
            db.rollback()
        finally:
            db.close()

    async def send_new_vacancies_to_users(self, new_vacancies_for_users: dict):
        """
        Отправка новых вакансий пользователям
        """
        for user_id, vacancies_data in new_vacancies_for_users.items():
            db: Session = next(get_db())
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    try:
                        # Отправляем сообщение с новыми вакансиями
                        message_text = f"Найдено {len(vacancies_data)} новых вакансий по вашему запросу:\n\n"
                        
                        for i, vacancy_data in enumerate(vacancies_data[:5]):  # Ограничиваем 5 вакансиями
                            vacancy = vacancy_data['vacancy']
                            salary_info = ""
                            if vacancy.salary_from or vacancy.salary_to:
                                salary_from = f"{vacancy.salary_from}" if vacancy.salary_from else "не указана"
                                salary_to = f"{vacancy.salary_to}" if vacancy.salary_to else "не указана"
                                salary_info = f"\n💰 Зарплата: {salary_from} - {salary_to} {vacancy.salary_currency or ''}"
                            
                            message_text += (
                                f"{i+1}. <b>{vacancy.title}</b>\n"
                                f"   🏢 {vacancy.company}\n"
                                f"   📍 {vacancy.city}{salary_info}\n"
                                f"   🔗 <a href='{vacancy.url}'>Ссылка на вакансию</a>\n\n"
                            )
                        
                        message_text += "Для просмотра всех вакансий и генерации резюме используйте команду /vacancies"
                        
                        await self.bot.send_message(user.telegram_id, message_text, parse_mode="HTML")
                        
                    except Exception as e:
                        print(f"Ошибка при отправке сообщения пользователю {user.telegram_id}: {e}")
            finally:
                db.close()