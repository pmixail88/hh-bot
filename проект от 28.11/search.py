from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

router = Router()

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

# Счетчики поиска
search_counters = {
    "it": 0,
    "production": 0,
    "finance": 0,
    "design": 0
}

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
    
    # Проверяем, что это действительно категория поиска
    if category not in search_counters:
        await callback.answer("❌ Неизвестная категория")
        return
    
    categories = {
        "it": "💼 IT-сфера",
        "production": "🏭 Производство", 
        "finance": "💰 Финансы",
        "design": "🎨 Дизайн"
    }
    
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