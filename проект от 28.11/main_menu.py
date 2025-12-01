from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command

from database import create_async_sessionmaker
from database.models import User

router = Router()

# Главное меню
def get_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Найти вакансии", callback_data="search_vacancies")],
            [InlineKeyboardButton(text="⭐ Мои вакансии", callback_data="my_vacancies")],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
            [InlineKeyboardButton(text="⚙️ Настройки поиска", callback_data="search_settings")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
        ]
    )

@router.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    
    # Сохраняем пользователя в базу
    async with create_async_sessionmaker() as session:
        db_user = await session.get(User, user.id)
        if not db_user:
            db_user = User(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            session.add(db_user)
            await session.commit()
    
    await message.answer(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я — <b>HH Work Day Bot</b> 🤖\n"
        f"Помогу найти тебе работу мечты на HH.ru!\n\n"
        f"<i>Выбери действие:</i>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    user = callback.from_user
    await callback.message.edit_text(
        f"🏠 <b>Главное меню</b>\n\n"
        f"Привет, {user.first_name}! 👋\n"
        f"Выбери действие:",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()