from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from database import create_async_sessionmaker
from database.models import User

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    async with create_async_sessionmaker() as session:
        # Проверяем есть ли пользователь в базе
        user = await session.get(User, message.from_user.id)
        
        if not user:
            # Создаем нового пользователя
            user = User(
                id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            session.add(user)
            await session.commit()
            
            await message.answer(
                "👋 Добро пожаловать в HH Work Day Bot!\n\n"
                "Я помогу вам найти работу на HH.ru и управлять вакансиями.\n\n"
                "Доступные команды:\n"
                "/profile - настройки профиля\n"
                "/search - поиск вакансий\n"
                "/favorites - избранные вакансии"
            )
        else:
            await message.answer(
                "🔄 С возвращением!\n\n"
                "Доступные команды:\n"
                "/profile - настройки профиля\n"
                "/search - поиск вакансий\n"
                "/favorites - избранные вакансии"
            )