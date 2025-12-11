from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from core.dependencies import DependencyProvider
from utils.keyboards import get_main_keyboard

router = Router()

@router.message(CommandStart())
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
        f"👋 Привет, {user.full_name}!\n\n"
        f"🚀 <b>HH Work Day Bot</b> - твой персональный помощник в поиске работы!\n\n"
        f"<b>Что я умею:</b>\n"
        f"• 🔍 Умный поиск вакансий с HeadHunter\n"
        f"• 💼 Автоматическое сохранение в базу данных\n"
        f"• ⚡ Быстрый кэш для мгновенного доступа\n"
        f"• 🤖 AI-анализ вакансий и генерация резюме\n"
        f"• ⏰ Автоматические уведомления о новых вакансиях\n\n"
        f"<b>Начни с настройки профиля и параметров поиска!</b>"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("stats"))
async def cmd_stats(message: Message, provider: DependencyProvider):
    """Статистика пользователя"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    stats = await provider.user_vacancy_repo.get_vacancy_stats(user.id)
    
    stats_text = (
        f"📊 <b>Ваша статистика:</b>\n\n"
        f"💼 Всего вакансий: <b>{stats['total']}</b>\n"
        f"⭐ В избранном: <b>{stats['favorites']}</b>\n"
        f"📨 Откликов: <b>{stats['applied']}</b>\n"
        f"👀 Непросмотренных: <b>{stats['unviewed']}</b>"
    )
    
    await message.answer(stats_text, parse_mode="HTML")