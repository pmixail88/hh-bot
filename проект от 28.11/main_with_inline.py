import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Меню поиска
def get_search_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💼 IT-сфера", callback_data="search_it")],
            [InlineKeyboardButton(text="🏭 Производство", callback_data="search_production")],
            [InlineKeyboardButton(text="💰 Финансы", callback_data="search_finance")],
            [InlineKeyboardButton(text="🎨 Дизайн", callback_data="search_design")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )

# Меню настроек
def get_settings_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏙️ Город", callback_data="set_city")],
            [InlineKeyboardButton(text="💵 Зарплата", callback_data="set_salary")],
            [InlineKeyboardButton(text="📅 Опыт работы", callback_data="set_experience")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )

# Счетчики для демонстрации (только для категорий поиска)
search_counters = {
    "it": 0,
    "production": 0,
    "finance": 0,
    "design": 0
}

@router.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    await message.answer(
        f"👋 Привет, {user.first_name}!\n\n"
        f"Я — <b>HH Work Day Bot</b> 🤖\n"
        f"Помогу найти тебе работу мечты на HH.ru!\n\n"
        f"<i>Выбери действие:</i>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    logger.info(f"Пользователь {user.id} запустил бота")

@router.callback_query(F.data == "search_vacancies")
async def search_vacancies(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔍 <b>Поиск вакансий</b>\n\n"
        "Выбери сферу для поиска:",
        reply_markup=get_search_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("search_"))
async def search_category(callback: CallbackQuery):
    category = callback.data.replace("search_", "")
    
    # Проверяем, что это действительно категория поиска, а не другие кнопки
    if category not in search_counters:
        await callback.answer("❌ Неизвестная категория")
        return
    
    categories = {
        "it": "💼 IT-сфера",
        "production": "🏭 Производство", 
        "finance": "💰 Финансы",
        "design": "🎨 Дизайн"
    }
    
    # Увеличиваем счетчик для этого типа поиска
    search_counters[category] += 1
    
    await callback.message.edit_text(
        f"🔍 Ищу вакансии в категории: <b>{categories[category]}</b>\n\n"
        f"📊 Поиск №{search_counters[category]}\n"
        f"⏳ Загружаю свежие вакансии...\n"
        f"💡 Совет: уточни настройки поиска для лучших результатов",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить поиск", callback_data=callback.data)],
                [InlineKeyboardButton(text="⚙️ Настройки", callback_data="search_settings")],
                [InlineKeyboardButton(text="🔙 Назад к поиску", callback_data="search_vacancies")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
            ]
        ),
        parse_mode="HTML"
    )
    await callback.answer(f"Ищем в {categories[category]}...")

@router.callback_query(F.data == "my_vacancies")
async def my_vacancies(callback: CallbackQuery):
    await callback.message.edit_text(
        "⭐ <b>Мои вакансии</b>\n\n"
        "📌 Сохраненные: <b>0</b>\n"
        "❤️ Понравившиеся: <b>0</b>\n"
        "📨 Отклики: <b>0</b>\n\n"
        "Здесь будут твои сохраненные вакансии",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💾 Сохраненные", callback_data="saved")],
                [InlineKeyboardButton(text="❤️ Избранные", callback_data="favorites")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ]
        ),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    user = callback.from_user
    await callback.message.edit_text(
        f"👤 <b>Твой профиль</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👁️ Имя: <b>{user.first_name}</b>\n"
        f"📛 Фамилия: <b>{user.last_name or 'не указана'}</b>\n"
        f"📱 Username: @{user.username or 'не указан'}\n\n"
        f"📊 Статистика:\n"
        f"• Найдено вакансий: <b>0</b>\n"
        f"• Сохранено: <b>0</b>\n"
        f"• Откликов: <b>0</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_profile")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ]
        ),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "search_settings")
async def search_settings(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚙️ <b>Настройки поиска</b>\n\n"
        "Настрой параметры для поиска вакансий:\n\n"
        "🏙️ Город: <b>Не указан</b>\n"
        "💵 Зарплата: <b>Не указана</b>\n"
        "📅 Опыт: <b>Не указан</b>\n\n"
        "💡 Укажи параметры для точного поиска",
        reply_markup=get_settings_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "stats")
async def stats(callback: CallbackQuery):
    total_searches = sum(search_counters.values())
    await callback.message.edit_text(
        "📊 <b>Статистика</b>\n\n"
        "📈 Твоя активность:\n"
        f"• Всего поисков: <b>{total_searches}</b>\n"
        f"• IT: <b>{search_counters['it']}</b>\n"
        f"• Финансы: <b>{search_counters['finance']}</b>\n"
        f"• Дизайн: <b>{search_counters['design']}</b>\n\n"
        "🎯 Эффективность:\n"
        "• Откликов: <b>0</b>\n"
        "• Приглашений: <b>0</b>",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="stats")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ]
        ),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "help")
async def help_command(callback: CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ <b>Помощь по боту</b>\n\n"
        "🤖 <b>HH Work Day Bot</b>\n\n"
        "📋 <b>Основные функции:</b>\n"
        "• 🔍 Поиск вакансий по категориям\n"
        "• ⭐ Сохранение понравившихся вакансий\n"
        "• 👤 Настройка профиля и предпочтений\n"
        "• 📊 Статистика поиска\n\n"
        "⚡ <b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n\n"
        "💡 <b>Совет:</b> Настрой параметры поиска для лучших результатов!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
            ]
        ),
        parse_mode="HTML"
    )
    await callback.answer()

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

# Обработчики для кнопок, которые еще не реализованы
@router.callback_query(F.data.in_(["saved", "favorites", "edit_profile", "set_city", "set_salary", "set_experience"]))
async def not_implemented(callback: CallbackQuery):
    await callback.answer("🚧 Этот функционал еще в разработке!", show_alert=True)

@router.message(Command("help"))
async def help_message(message: Message):
    await message.answer(
        "ℹ️ Используй кнопки меню для навигации!\n"
        "Или напиши /start для главного меню."
    )

@router.message()
async def any_message(message: Message):
    await message.answer(
        "🤖 Используй кнопки меню или команды!\n"
        "Напиши /start для открытия главного меню."
    )

async def main():
    # ⚠️ ЗАМЕНИ НА СВОЙ ТОКЕН!
    BOT_TOKEN = "7128969872:AAH0w4P9h5Wm8c8M9P6cR7YqXq9Z8wQxXxX"
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    logger.info("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())