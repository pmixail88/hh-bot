from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from bot.db.database import get_db
from bot.db.models import User, SearchFilter
from sqlalchemy.orm import Session
from typing import Optional


router = Router()


@router.message(Command("search_settings"))
async def cmd_search_settings(message: Message):
    """
    Обработчик команды /search_settings
    Позволяет пользователю настроить фильтры поиска вакансий
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        # Проверяем, существует ли пользователь
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Проверяем, есть ли у пользователя уже активные фильтры
        existing_filter = db.query(SearchFilter).filter(
            SearchFilter.user_id == user.id,
            SearchFilter.is_active == True
        ).first()
        
        if existing_filter:
            # Отображаем текущие настройки
            await message.answer(
                f"Ваши текущие настройки поиска:\n"
                f"Должность: {existing_filter.position or 'Не указана'}\n"
                f"Город: {existing_filter.city or 'Не указан'}\n"
                f"Минимальная зарплата: {existing_filter.min_salary or 'Не указана'}\n"
                f"Тип занятости: {existing_filter.employment_types or 'Любой'}\n"
                f"Опыт работы: {existing_filter.experience_level or 'Любой'}\n\n"
                f"Для изменения настроек введите новые значения по одному за раз:\n"
                f"1. /set_position - Установить желаемую должность\n"
                f"2. /set_city - Установить город\n"
                f"3. /set_min_salary - Установить минимальную зарплату\n"
                f"4. /set_employment - Установить тип занятости\n"
                f"5. /set_experience - Установить требуемый опыт\n"
                f"6. /set_filters - Установить все фильтры разом"
            )
        else:
            # Создаем новый фильтр для пользователя
            new_filter = SearchFilter(
                user_id=user.id,
                position="",
                city="",
                min_salary=None,
                metro_stations="",
                freshness_days=3,
                employment_types="",
                experience_level="",
                only_direct_employers=False,
                company_size="",
                only_top_companies=False
            )
            
            db.add(new_filter)
            db.commit()
            
            await message.answer(
                f"Настройки поиска вакансий.\n\n"
                f"Введите желаемую должность, или используйте команды:\n"
                f"1. /set_position - Установить желаемую должность\n"
                f"2. /set_city - Установить город\n"
                f"3. /set_min_salary - Установить минимальную зарплату\n"
                f"4. /set_employment - Установить тип занятости\n"
                f"5. /set_experience - Установить требуемый опыт\n"
                f"6. /set_filters - Установить все фильтры разом"
            )
    
    finally:
        db.close()


@router.message(Command("set_position"))
async def cmd_set_position(message: Message):
    """
    Установка желаемой должности
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Получаем текст после команды
        position = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not position:
            await message.answer("Пожалуйста, укажите должность после команды. Пример: /set_position Python разработчик")
            return
        
        # Обновляем фильтр
        search_filter = db.query(SearchFilter).filter(
            SearchFilter.user_id == user.id,
            SearchFilter.is_active == True
        ).first()
        
        if search_filter:
            search_filter.position = position
            db.commit()
            await message.answer(f"Желаемая должность установлена: {position}")
        else:
            await message.answer("Сначала настройте фильтры с помощью команды /search_settings")
    
    finally:
        db.close()


@router.message(Command("set_city"))
async def cmd_set_city(message: Message):
    """
    Установка города
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Получаем текст после команды
        city = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not city:
            await message.answer("Пожалуйста, укажите город после команды. Пример: /set_city Москва")
            return
        
        # Обновляем фильтр
        search_filter = db.query(SearchFilter).filter(
            SearchFilter.user_id == user.id,
            SearchFilter.is_active == True
        ).first()
        
        if search_filter:
            search_filter.city = city
            db.commit()
            await message.answer(f"Город установлен: {city}")
        else:
            await message.answer("Сначала настройте фильтры с помощью команды /search_settings")
    
    finally:
        db.close()


@router.message(Command("set_min_salary"))
async def cmd_set_min_salary(message: Message):
    """
    Установка минимальной зарплаты
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Получаем текст после команды
        salary_str = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not salary_str:
            await message.answer("Пожалуйста, укажите минимальную зарплату после команды. Пример: /set_min_salary 100000")
            return
        
        try:
            salary = int(salary_str)
            if salary < 0:
                raise ValueError("Зарплата не может быть отрицательной")
        except ValueError:
            await message.answer("Пожалуйста, укажите корректное число для зарплаты. Пример: /set_min_salary 100000")
            return
        
        # Обновляем фильтр
        search_filter = db.query(SearchFilter).filter(
            SearchFilter.user_id == user.id,
            SearchFilter.is_active == True
        ).first()
        
        if search_filter:
            search_filter.min_salary = salary
            db.commit()
            await message.answer(f"Минимальная зарплата установлена: {salary}")
        else:
            await message.answer("Сначала настройте фильтры с помощью команды /search_settings")
    
    finally:
        db.close()


@router.message(Command("set_employment"))
async def cmd_set_employment(message: Message):
    """
    Установка типа занятости
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Получаем текст после команды
        employment = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not employment:
            await message.answer(
                "Пожалуйста, укажите тип занятости после команды.\n"
                "Доступные значения: full (полная), part (частичная), project (проектная), remote (удаленная).\n"
                "Пример: /set_employment full,remote"
            )
            return
        
        # Обновляем фильтр
        search_filter = db.query(SearchFilter).filter(
            SearchFilter.user_id == user.id,
            SearchFilter.is_active == True
        ).first()
        
        if search_filter:
            search_filter.employment_types = employment
            db.commit()
            await message.answer(f"Тип занятости установлен: {employment}")
        else:
            await message.answer("Сначала настройте фильтры с помощью команды /search_settings")
    
    finally:
        db.close()


@router.message(Command("set_experience"))
async def cmd_set_experience(message: Message):
    """
    Установка требуемого опыта
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Получаем текст после команды
        experience = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not experience:
            await message.answer(
                "Пожалуйста, укажите требуемый опыт после команды.\n"
                "Доступные значения: noExperience (без опыта), between1And3 (1-3 года), between3And6 (3-6 лет), moreThan6 (более 6 лет).\n"
                "Пример: /set_experience between1And3"
            )
            return
        
        # Проверяем допустимые значения
        valid_experiences = ["noExperience", "between1And3", "between3And6", "moreThan6"]
        if experience not in valid_experiences:
            await message.answer(
                f"Недопустимое значение опыта. Доступные значения: {', '.join(valid_experiences)}"
            )
            return
        
        # Обновляем фильтр
        search_filter = db.query(SearchFilter).filter(
            SearchFilter.user_id == user.id,
            SearchFilter.is_active == True
        ).first()
        
        if search_filter:
            search_filter.experience_level = experience
            db.commit()
            await message.answer(f"Требуемый опыт установлен: {experience}")
        else:
            await message.answer("Сначала настройте фильтры с помощью команды /search_settings")
    
    finally:
        db.close()