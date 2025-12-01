from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from core.dependencies import DependencyProvider
from utils.states import ProfileStates
from utils.keyboards import get_back_to_menu_keyboard

router = Router()

@router.callback_query(F.data == "menu_profile")
async def show_profile(callback: CallbackQuery, provider: DependencyProvider):
    """Показать профиль пользователя"""
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    profile_text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"📛 <b>Имя:</b> {user.full_name or 'Не указано'}\n"
        f"🏙️ <b>Город:</b> {user.city or 'Не указан'}\n"
        f"💼 <b>Желаемая должность:</b> {user.desired_position or 'Не указана'}\n"
        f"🛠️ <b>Навыки:</b> {user.skills or 'Не указаны'}\n"
        f"📄 <b>Резюме:</b> {'✅ Указано' if user.base_resume else '❌ Не указано'}\n\n"
        f"⏰ <b>Автопроверка:</b> {'✅ Включена' if user.scheduler_enabled else '❌ Выключена'}\n"
        f"🕐 <b>Время проверок:</b> {user.scheduler_times}\n"
        f"🔄 <b>Интервал:</b> каждые {user.check_interval_hours} часов"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Имя", callback_data="profile_edit_name"),
            InlineKeyboardButton(text="🏙️ Город", callback_data="profile_edit_city")
        ],
        [
            InlineKeyboardButton(text="💼 Должность", callback_data="profile_edit_position"),
            InlineKeyboardButton(text="🛠️ Навыки", callback_data="profile_edit_skills")
        ],
        [
            InlineKeyboardButton(text="📄 Резюме", callback_data="profile_edit_resume"),
            InlineKeyboardButton(text="⏰ Расписание", callback_data="profile_edit_schedule")
        ],
        [
            InlineKeyboardButton(text="📊 Главное меню", callback_data="menu_main")
        ]
    ])
    
    await callback.message.edit_text(profile_text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("profile_edit_"))
async def handle_profile_edit(callback: CallbackQuery, state: FSMContext):
    """Обработчик редактирования профиля"""
    action = callback.data.replace("profile_edit_", "")
    
    state_mapping = {
        "name": (ProfileStates.waiting_name, "✏️ Введите ваше имя и фамилию:"),
        "city": (ProfileStates.waiting_city, "🏙️ Введите ваш город:"),
        "position": (ProfileStates.waiting_position, "💼 Введите желаемую должность:"),
        "skills": (ProfileStates.waiting_skills, "🛠️ Введите ваши навыки:"),
        "resume": (ProfileStates.waiting_resume, "📄 Введите текст вашего резюме:"),
        "schedule": (ProfileStates.waiting_schedule, "⏰ Настройте расписание проверок:")
    }
    
    if action in state_mapping:
        state_class, message_text = state_mapping[action]
        await state.set_state(state_class)
        await callback.message.edit_text(
            f"{message_text}\n\n<i>Отправьте текст или нажмите 'Отмена' для возврата</i>",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    await callback.answer()

@router.message(ProfileStates.waiting_name)
async def process_name(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода имени"""
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        full_name=message.text
    )
    await message.answer("✅ Имя успешно обновлено!")
    await state.clear()
    await show_profile(message, provider)

@router.message(ProfileStates.waiting_city)
async def process_city(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода города"""
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        city=message.text
    )
    await message.answer("✅ Город успешно обновлен!")
    await state.clear()
    await show_profile(message, provider)

@router.message(ProfileStates.waiting_position)
async def process_position(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода должности"""
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        desired_position=message.text
    )
    await message.answer("✅ Должность успешно обновлена!")
    await state.clear()
    await show_profile(message, provider)

@router.message(ProfileStates.waiting_skills)
async def process_skills(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода навыков"""
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        skills=message.text
    )
    await message.answer("✅ Навыки успешно обновлены!")
    await state.clear()
    await show_profile(message, provider)

@router.message(ProfileStates.waiting_resume)
async def process_resume(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода резюме"""
    await provider.user_repo.update_user_profile(
        str(message.from_user.id),
        base_resume=message.text
    )
    await message.answer("✅ Резюме успешно обновлено!")
    await state.clear()
    await show_profile(message, provider)

async def show_profile(message: Message, provider: DependencyProvider):
    """Вспомогательная функция для показа профиля (для использования из message)"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    
    if not user:
        await message.answer("❌ Пользователь не найден")
        return
    
    profile_text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"📛 <b>Имя:</b> {user.full_name or 'Не указано'}\n"
        f"🏙️ <b>Город:</b> {user.city or 'Не указан'}\n"
        f"💼 <b>Желаемая должность:</b> {user.desired_position or 'Не указана'}\n"
        f"🛠️ <b>Навыки:</b> {user.skills or 'Не указаны'}\n"
        f"📄 <b>Резюме:</b> {'✅ Указано' if user.base_resume else '❌ Не указано'}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="menu_profile"),
            InlineKeyboardButton(text="📊 Главное меню", callback_data="menu_main")
        ]
    ])
    
    await message.answer(profile_text, reply_markup=keyboard, parse_mode="HTML")