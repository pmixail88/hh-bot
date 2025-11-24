from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.db.database import get_db
from bot.db.models import User
from sqlalchemy.orm import Session


router = Router()


@router.message(Command("my_profile"))
async def cmd_my_profile(message: Message):
    """
    Обработчик команды /my_profile
    Позволяет пользователю посмотреть и отредактировать свой профиль
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        # Проверяем, существует ли пользователь
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Отображаем текущий профиль
        await message.answer(
            f"Ваш профиль:\n"
            f"Имя: {user.full_name}\n"
            f"Город: {user.city or 'Не указан'}\n"
            f"Желаемая должность: {user.desired_position or 'Не указана'}\n"
            f"Навыки: {user.skills or 'Не указаны'}\n"
            f"Базовое резюме: {user.base_resume or 'Не указано'}\n\n"
            f"Для изменения данных используйте команды:\n"
            f"/update_city - Обновить город\n"
            f"/update_position - Обновить желаемую должность\n"
            f"/update_skills - Обновить навыки\n"
            f"/update_resume - Обновить базовое резюме"
        )
    
    finally:
        db.close()


@router.message(Command("update_city"))
async def cmd_update_city(message: Message):
    """
    Обновление города пользователя
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
            await message.answer("Пожалуйста, укажите город после команды. Пример: /update_city Санкт-Петербург")
            return
        
        user.city = city
        db.commit()
        
        await message.answer(f"Город обновлен: {city}")
    
    finally:
        db.close()


@router.message(Command("update_position"))
async def cmd_update_position(message: Message):
    """
    Обновление желаемой должности пользователя
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
            await message.answer("Пожалуйста, укажите должность после команды. Пример: /update_position Python разработчик")
            return
        
        user.desired_position = position
        db.commit()
        
        await message.answer(f"Желаемая должность обновлена: {position}")
    
    finally:
        db.close()


@router.message(Command("update_skills"))
async def cmd_update_skills(message: Message):
    """
    Обновление навыков пользователя
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Получаем текст после команды
        skills = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not skills:
            await message.answer("Пожалуйста, укажите навыки после команды. Пример: /update_skills Python, SQL, Docker")
            return
        
        user.skills = skills
        db.commit()
        
        await message.answer(f"Навыки обновлены: {skills}")
    
    finally:
        db.close()


@router.message(Command("update_resume"))
async def cmd_update_resume(message: Message):
    """
    Обновление базового резюме пользователя
    """
    user_id = message.from_user.id
    db: Session = next(get_db())
    
    try:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        
        if not user:
            await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start")
            return
        
        # Получаем текст после команды
        resume = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
        
        if not resume:
            await message.answer("Пожалуйста, укажите резюме после команды. Пример: /update_resume Опытный разработчик...")
            return
        
        user.base_resume = resume
        db.commit()
        
        await message.answer("Базовое резюме обновлено!")
    
    finally:
        db.close()