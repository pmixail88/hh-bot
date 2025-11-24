from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.db.database import get_db
from bot.db.models import User, Vacancy, UserVacancy, GeneratedDocument
from bot.services.hh_service import HHService
from bot.services.llm_service import LLMService
from sqlalchemy.orm import Session
from typing import List
import json


router = Router()
hh_service = HHService()
llm_service = LLMService()


@router.message(Command("vacancies"))
async def cmd_vacancies(message: Message):
    """
    Обработчик команды /vacancies
    Показывает пользователю подборку вакансий по его фильтрам
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        # Проверяем, существует ли пользователь
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Получаем фильтры пользователя
        from bot.db.models import SearchFilter
        user_filter = db.query(SearchFilter).filter(
            SearchFilter.user_id == user.id,
            SearchFilter.is_active == True
        ).first()
        
        if not user_filter:
            await message.answer(
                "У вас нет активных фильтров поиска. "
                "Настройте их с помощью команды /search_settings"
            )
            return
        
        # Получаем вакансии для пользователя из базы данных
        # Берем только те, которые еще не были показаны пользователю или были показаны более 24 часов назад
        from datetime import datetime, timedelta
        time_threshold = datetime.utcnow() - timedelta(hours=24)
        
        user_vacancies = db.query(UserVacancy).filter(
            UserVacancy.user_id == user.id,
            UserVacancy.viewed_at >= time_threshold
        ).all()
        
        viewed_vacancy_ids = [uv.vacancy_id for uv in user_vacancies]
        
        # Получаем вакансии, которые пользователь еще не видел или которые были показаны давно
        all_user_vacancies = db.query(Vacancy).join(UserVacancy).filter(
            UserVacancy.user_id == user.id,
            ~Vacancy.id.in_(viewed_vacancy_ids)  # Исключаем уже просмотренные
        ).limit(5).all()  # Ограничиваем до 5 вакансий
        
        if not all_user_vacancies:
            # Если нет новых вакансий в базе, пробуем получить свежие с HH.ru
            fresh_vacancies = hh_service.search_vacancies(
                text=user_filter.position,
                city=user_filter.city,
                salary=user_filter.min_salary,
                employment=user_filter.employment_types.split(',') if user_filter.employment_types else None,
                experience=user_filter.experience_level,
                period=user_filter.freshness_days,
                employer_type='direct' if user_filter.only_direct_employers else None,
                company_size=user_filter.company_size if user_filter.company_size else None
            )
            
            # Сохраняем свежие вакансии в базу
            for vacancy_data in fresh_vacancies:
                existing_vacancy = db.query(Vacancy).filter(Vacancy.hh_id == vacancy_data['id']).first()
                
                if not existing_vacancy:
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
                    db.flush()
                    
                    # Создаем связь с пользователем
                    user_vacancy = UserVacancy(
                        user_id=user.id,
                        vacancy_id=new_vacancy.id,
                        is_interesting=True
                    )
                    
                    db.add(user_vacancy)
            
            db.commit()
            
            # Повторно получаем вакансии
            all_user_vacancies = db.query(Vacancy).join(UserVacancy).filter(
                UserVacancy.user_id == user.id,
                ~Vacancy.id.in_(viewed_vacancy_ids)  # Исключаем уже просмотренные
            ).limit(5).all()
        
        if all_user_vacancies:
            for vacancy in all_user_vacancies:
                # Обновляем время просмотра
                user_vacancy = db.query(UserVacancy).filter(
                    UserVacancy.user_id == user.id,
                    UserVacancy.vacancy_id == vacancy.id
                ).first()
                
                if user_vacancy:
                    user_vacancy.viewed_at = datetime.utcnow()
                    db.commit()
                
                # Формируем сообщение с вакансией
                salary_info = ""
                if vacancy.salary_from or vacancy.salary_to:
                    salary_from = f"{vacancy.salary_from}" if vacancy.salary_from else "не указана"
                    salary_to = f"{vacancy.salary_to}" if vacancy.salary_to else "не указана"
                    salary_info = f"\n💰 Зарплата: {salary_from} - {salary_to} {vacancy.salary_currency or ''}"
                
                message_text = (
                    f"💼 <b>{vacancy.title}</b>\n"
                    f"🏢 {vacancy.company}\n"
                    f"📍 {vacancy.city}{salary_info}\n"
                    f"📋 {vacancy.description}\n"
                    f"🔗 <a href='{vacancy.url}'>Ссылка на вакансию</a>"
                )
                
                # Отправляем сообщение с inline-кнопками
                from aiogram.utils.keyboard import InlineKeyboardBuilder
                from aiogram.types import InlineKeyboardButton
                
                keyboard = InlineKeyboardBuilder()
                keyboard.add(
                    InlineKeyboardButton(
                        text="📝 Сгенерировать резюме", 
                        callback_data=f"resume_{vacancy.id}"
                    )
                )
                keyboard.add(
                    InlineKeyboardButton(
                        text="📄 Сгенерировать cover letter", 
                        callback_data=f"cover_{vacancy.id}"
                    )
                )
                keyboard.add(
                    InlineKeyboardButton(
                        text="👎 Неинтересно", 
                        callback_data=f"not_interesting_{vacancy.id}"
                    )
                )
                
                await message.answer(
                    message_text, 
                    reply_markup=keyboard.as_markup(),
                    parse_mode="HTML"
                )
        else:
            await message.answer("Пока нет подходящих вакансий. Попробуйте изменить параметры поиска.")
    
    finally:
        db.close()


@router.callback_query(F.data.startswith('resume_'))
async def callback_generate_resume(callback: CallbackQuery):
    """
    Генерация резюме для выбранной вакансии
    """
    vacancy_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await callback.answer("Пожалуйста, сначала зарегистрируйтесь", show_alert=True)
            return
        
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        
        if not vacancy:
            await callback.answer("Вакансия не найдена", show_alert=True)
            return
        
        # Подготовим данные пользователя и вакансии
        user_profile = {
            'full_name': user.full_name,
            'skills': user.skills,
            'base_resume': user.base_resume
        }
        
        vacancy_info = {
            'title': vacancy.title,
            'company': vacancy.company,
            'city': vacancy.city,
            'salary_from': vacancy.salary_from,
            'salary_to': vacancy.salary_to,
            'salary_currency': vacancy.salary_currency,
            'description': vacancy.description
        }
        
        # Генерируем резюме
        resume = llm_service.generate_resume(user_profile, vacancy_info)
        
        if resume:
            # Сохраняем сгенерированное резюме
            generated_doc = GeneratedDocument(
                user_id=user.id,
                vacancy_id=vacancy.id,
                document_type='resume',
                content=resume
            )
            
            db.add(generated_doc)
            
            # Отмечаем, что резюме было сгенерировано
            user_vacancy = db.query(UserVacancy).filter(
                UserVacancy.user_id == user.id,
                UserVacancy.vacancy_id == vacancy.id
            ).first()
            
            if user_vacancy:
                user_vacancy.resume_generated = True
            
            db.commit()
            
            # Отправляем резюме пользователю
            await callback.message.answer(f"Ваше персонализированное резюме:\n\n{resume}")
            await callback.answer("Резюме сгенерировано!")
        else:
            await callback.answer("Не удалось сгенерировать резюме. Попробуйте позже.", show_alert=True)
    
    finally:
        db.close()


@router.callback_query(F.data.startswith('cover_'))
async def callback_generate_cover_letter(callback: CallbackQuery):
    """
    Генерация сопроводительного письма для выбранной вакансии
    """
    vacancy_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await callback.answer("Пожалуйста, сначала зарегистрируйтесь", show_alert=True)
            return
        
        vacancy = db.query(Vacancy).filter(Vacancy.id == vacancy_id).first()
        
        if not vacancy:
            await callback.answer("Вакансия не найдена", show_alert=True)
            return
        
        # Подготовим данные пользователя и вакансии
        user_profile = {
            'full_name': user.full_name,
            'skills': user.skills,
            'base_resume': user.base_resume
        }
        
        vacancy_info = {
            'title': vacancy.title,
            'company': vacancy.company,
            'city': vacancy.city,
            'salary_from': vacancy.salary_from,
            'salary_to': vacancy.salary_to,
            'salary_currency': vacancy.salary_currency,
            'description': vacancy.description
        }
        
        # Генерируем сопроводительное письмо
        cover_letter = llm_service.generate_cover_letter(user_profile, vacancy_info)
        
        if cover_letter:
            # Сохраняем сгенерированное письмо
            generated_doc = GeneratedDocument(
                user_id=user.id,
                vacancy_id=vacancy.id,
                document_type='cover_letter',
                content=cover_letter
            )
            
            db.add(generated_doc)
            
            # Отмечаем, что письмо было сгенерировано
            user_vacancy = db.query(UserVacancy).filter(
                UserVacancy.user_id == user.id,
                UserVacancy.vacancy_id == vacancy.id
            ).first()
            
            if user_vacancy:
                user_vacancy.cover_letter_generated = True
            
            db.commit()
            
            # Отправляем письмо пользователю
            await callback.message.answer(f"Ваше сопроводительное письмо:\n\n{cover_letter}")
            await callback.answer("Сопроводительное письмо сгенерировано!")
        else:
            await callback.answer("Не удалось сгенерировать сопроводительное письмо. Попробуйте позже.", show_alert=True)
    
    finally:
        db.close()


@router.callback_query(F.data.startswith('not_interesting_'))
async def callback_mark_not_interesting(callback: CallbackQuery):
    """
    Отметить вакансию как неинтересную
    """
    vacancy_id = int(callback.data.split('_')[2])
    user_id = callback.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await callback.answer("Пожалуйста, сначала зарегистрируйтесь", show_alert=True)
            return
        
        # Отмечаем вакансию как неинтересную
        user_vacancy = db.query(UserVacancy).filter(
            UserVacancy.user_id == user.id,
            UserVacancy.vacancy_id == vacancy_id
        ).first()
        
        if user_vacancy:
            user_vacancy.is_interesting = False
            db.commit()
        
        await callback.answer("Вакансия отмечена как неинтересная")
        await callback.message.edit_reply_markup(reply_markup=None)  # Убираем кнопки
    
    finally:
        db.close()