from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "ℹ️ Помощь по боту:\n\n"
        "/start - начать работу\n"
        "/profile - настройки профиля\n"
        "/search - поиск вакансий\n"
        "/favorites - избранные вакансии\n"
        "/help - показать эту справку"
    )

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Обработчик команды /profile"""
    await message.answer(
        "👤 Настройки профиля:\n\n"
        "Здесь вы можете настроить параметры поиска вакансий.\n"
        "Функционал в разработке..."
    )

@router.message()
async def echo_handler(message: Message):
    """Обработчик любых сообщений"""
    await message.answer(
        "🤖 Я не понимаю эту команду.\n"
        "Используйте /help для списка доступных команд."
    )