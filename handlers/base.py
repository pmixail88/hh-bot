from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from core.dependencies import DependencyProvider
from utils.keyboards import get_main_keyboard
from utils.logger import get_logger

logger = get_logger(__name__)  # Добавить
router = Router()

@router.message(Command("start"))
async def cmd_start(
    message: Message, 
    provider: DependencyProvider,
    state: FSMContext
):
    """Обработчик команды /start"""
    user_id = str(message.from_user.id)
    full_name = message.from_user.full_name
    
    # Получаем или создаем пользователя
    user = await provider.user_repo.get_or_create_user(
        telegram_id=user_id,
        full_name=full_name,
        username=message.from_user.username
    )
    
    await state.clear()
    
    welcome_text = (
        f"👋 Привет, {user.full_name}!\n"
        f"Добро пожаловать в <b>HH Work Day Bot</b> - вашего помощника в поиске работы!\n\n"
        f"📊 <b>Главное меню</b> - выберите действие:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
🤖 <b>Помощь по HH Work Day Bot</b>

<b>Основные команды:</b>
/start - Начать работу с ботом
/help - Показать эту справку
/menu - Главное меню

<b>Возможности:</b>
🔍 <b>Настроить поиск</b> - установить параметры поиска вакансий
👤 <b>Мой профиль</b> - просмотр и редактирование профиля
💼 <b>Новые вакансии</b> - поиск свежих вакансий по вашим настройкам
🤖 <b>Настройка AI</b> - настройка интеллектуального анализа вакансий
📂 <b>Мои вакансии</b> - просмотр сохраненных вакансий
⏰ <b>Расписание</b> - настройка автоматической проверки

<b>Как работать:</b>
1. Настройте параметры поиска
2. Ищите вакансии
3. Сохраняйте интересные предложения
4. Используйте AI для анализа вакансий
    """
    await message.answer(help_text, parse_mode="HTML")

@router.message(Command("menu"))
async def cmd_menu(message: Message, provider: DependencyProvider):
    """Показать главное меню"""
    user_id = str(message.from_user.id)
    user = await provider.user_repo.get_user_by_telegram_id(user_id)
    
    user_name = user.full_name if user else "Пользователь"
    
    await message.answer(
        f"👋 Привет, {user_name}!\n"
        f"📊 <b>Главное меню HH Work Day Bot</b> - выберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "menu_main")
async def handle_menu_main(
    callback: CallbackQuery, 
    state: FSMContext,
    provider: DependencyProvider
):
    """Обработчик возврата в главное меню"""
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    
    user_id = str(callback.from_user.id)
    user = await provider.user_repo.get_user_by_telegram_id(user_id)
    
    user_name = user.full_name if user else "Пользователь"
    
    await callback.message.answer(
        f"👋 Привет, {user_name}!\n"
        f"📊 <b>Главное меню HH Work Day Bot</b> - выберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
    
# bot/handlers/base.py - добавить в конец файла
@router.callback_query(F.data == "menu_stats")
async def show_statistics(callback: CallbackQuery, provider: DependencyProvider):
    """Показать статистику"""
    try:
        user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        stats = await provider.user_vacancy_repo.get_vacancy_stats(user.id)
        
        stats_text = (
            "📊 <b>Ваша статистика</b>\n\n"
            f"💼 Всего вакансий: <b>{stats['total']}</b>\n"
            f"⭐ Избранных: <b>{stats['favorites']}</b>\n"
            f"📨 Откликов: <b>{stats['applied']}</b>\n"
            f"👀 Непросмотренных: <b>{stats['unviewed']}</b>\n\n"
            f"💡 Совет: Регулярно проверяйте новые вакансии!"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Новый поиск", callback_data="menu_vacancies")],
            [InlineKeyboardButton(text="📂 Мои вакансии", callback_data="menu_my_vacancies")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_main")]
        ])
        
        #await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="HTML")
        await callback.message.edit_text(
            stats_text, 
            reply_markup=keyboard, 
            parse_mode="HTML"
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка при показе статистики: {e}")
        await callback.answer("❌ Ошибка при получении статистики", show_alert=True)

@router.callback_query(F.data == "menu_help")
async def show_help(callback: CallbackQuery):
    """Показать помощь"""
    help_text = """
🤖 <b>Помощь по HH Work Day Bot</b>

<b>Основные команды:</b>
/start - Начать работу с ботом
/help - Показать эту справку
/menu - Главное меню

<b>Возможности:</b>
🔍 <b>Настроить поиск</b> - установить параметры поиска вакансий
👤 <b>Мой профиль</b> - просмотр и редактирование профиля
💼 <b>Новые вакансии</b> - поиск свежих вакансий по вашим настройкам
🤖 <b>Настройка AI</b> - настройка интеллектуального анализа вакансий
📂 <b>Мои вакансии</b> - просмотр сохраненных вакансий
⏰ <b>Расписание</b> - настройка автоматической проверки

<b>Как работать:</b>
1. Настройте параметры поиска
2. Ищите вакансии
3. Сохраняйте интересные предложения
4. Используйте AI для анализа вакансий
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_main")]
    ])
    
    await callback.message.edit_text(
        help_text, 
        reply_markup=keyboard, 
        parse_mode="HTML"
    )
    await callback.answer()

'''    
@router.callback_query(F.data == "menu_responses")
async def show_responses_vacancy(callback: CallbackQuery, provider: DependencyProvider):
    """Отклик на вакансию из меню"""
    await callback.answer("Функция отклика на вакансию в разработке.", show_alert=True)
'''