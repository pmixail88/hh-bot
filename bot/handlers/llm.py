from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from core.dependencies import DependencyProvider
from utils.states import LLMStates
from utils.keyboards import get_back_to_menu_keyboard

router = Router()

@router.callback_query(F.data == "menu_llm_settings")
async def show_llm_settings(callback: CallbackQuery, provider: DependencyProvider):
    """Показать настройки AI"""
    user = await provider.user_repo.get_user_by_telegram_id(str(callback.from_user.id))
    llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
    
    if not llm_settings:
        await callback.answer("❌ Настройки AI не найдены", show_alert=True)
        return

    api_key_status = "❌ Не установлен"
    if llm_settings.api_key:
        if len(llm_settings.api_key) > 8:
            api_key_status = f"✅ Установлен ({llm_settings.api_key[:8]}...)"
        else:
            api_key_status = "✅ Установлен"

    settings_text = (
        "🤖 <b>Настройки AI помощника</b>\n\n"
        f"🌐 <b>Base URL:</b> {llm_settings.base_url or 'Не установлен'}\n"
        f"🔑 <b>API Key:</b> {api_key_status}\n"
        f"⚙️ <b>Model:</b> {llm_settings.model_name or 'Не установлена'}\n"
        f"🌡️ <b>Temperature:</b> {llm_settings.temperature}\n"
        f"📝 <b>Max Tokens:</b> {llm_settings.max_tokens}\n\n"
        f"📋 <b>Функции:</b>\n"
        f"• Генерация резюме: {'✅' if llm_settings.enable_resume_generation else '❌'}\n"
        f"• Сопроводительные письма: {'✅' if llm_settings.enable_cover_letter_generation else '❌'}\n"
        f"• Анализ вакансий: {'✅' if llm_settings.enable_vacancy_analysis else '❌'}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔑 API Key", callback_data="llm_edit_api_key"),
            InlineKeyboardButton(text="🌐 Base URL", callback_data="llm_edit_base_url")
        ],
        [
            InlineKeyboardButton(text="⚙️ Model", callback_data="llm_edit_model"),
            InlineKeyboardButton(text="🌡️ Temperature", callback_data="llm_edit_temperature")
        ],
        [
            InlineKeyboardButton(text="📊 Главное меню", callback_data="menu_main")
        ]
    ])
    
    await callback.message.edit_text(settings_text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("llm_edit_"))
async def handle_llm_edit(callback: CallbackQuery, state: FSMContext):
    """Обработчик редактирования настроек LLM"""
    setting = callback.data.replace("llm_edit_", "")
    
    state_mapping = {
        "api_key": (LLMStates.waiting_api_key, "🔑 Введите ваш API ключ:"),
        "base_url": (LLMStates.waiting_base_url, "🌐 Введите Base URL:"),
        "model": (LLMStates.waiting_model, "⚙️ Введите название модели:"),
        "temperature": (LLMStates.waiting_temperature, "🌡️ Введите значение temperature (0.0-1.0):")
    }
    
    if setting in state_mapping:
        state_class, message_text = state_mapping[setting]
        await state.set_state(state_class)
        await callback.message.edit_text(
            f"{message_text}\n\n<i>Отправьте значение или нажмите 'Отмена' для возврата</i>",
            reply_markup=get_back_to_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Неизвестная настройка", show_alert=True)

@router.message(LLMStates.waiting_api_key)
async def process_api_key(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода API ключа"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
    
    await provider.llm_settings_repo.update_settings(llm_settings.id, api_key=message.text)
    await message.answer("✅ API ключ сохранен!")
    await state.clear()
    # Используем вспомогательную функцию для показа настроек
    await _show_llm_settings_message(message, provider)

@router.message(LLMStates.waiting_base_url)
async def process_base_url(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода Base URL"""
    if not message.text.startswith(('http://', 'https://')):
        await message.answer("❌ URL должен начинаться с http:// или https://")
        return
        
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
    
    await provider.llm_settings_repo.update_settings(llm_settings.id, base_url=message.text)
    await message.answer("✅ Base URL сохранен!")
    await state.clear()
    await _show_llm_settings_message(message, provider)

@router.message(LLMStates.waiting_model)
async def process_model(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода модели"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
    
    await provider.llm_settings_repo.update_settings(llm_settings.id, model_name=message.text)
    await message.answer("✅ Модель сохранена!")
    await state.clear()
    await _show_llm_settings_message(message, provider)

@router.message(LLMStates.waiting_temperature)
async def process_temperature(message: Message, state: FSMContext, provider: DependencyProvider):
    """Обработка ввода температуры"""
    try:
        temperature = float(message.text)
        if not 0.0 <= temperature <= 1.0:
            await message.answer("❌ Temperature должен быть между 0.0 и 1.0")
            return
    except ValueError:
        await message.answer("❌ Введите число (например: 0.7)")
        return
        
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
    
    await provider.llm_settings_repo.update_settings(llm_settings.id, temperature=temperature)
    await message.answer("✅ Temperature сохранен!")
    await state.clear()
    await _show_llm_settings_message(message, provider)

async def _show_llm_settings_message(message: Message, provider: DependencyProvider):
    """Вспомогательная функция для показа настроек LLM (для использования из message)"""
    user = await provider.user_repo.get_user_by_telegram_id(str(message.from_user.id))
    llm_settings = await provider.llm_settings_repo.get_by_user_id(user.id)
    
    api_key_status = "❌ Не установлен"
    if llm_settings.api_key:
        api_key_status = "✅ Установлен"
    
    settings_text = (
        "🤖 <b>Настройки LLM</b>\n\n"
        f"🌐 <b>Base URL:</b> {llm_settings.base_url or 'Не установлен'}\n"
        f"🔑 <b>API Key:</b> {api_key_status}\n"
        f"⚙️ <b>Model:</b> {llm_settings.model_name or 'Не установлена'}\n"
        f"🌡️ <b>Temperature:</b> {llm_settings.temperature}\n"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔑 Настроить", callback_data="menu_llm_settings"),
            InlineKeyboardButton(text="📊 Главное меню", callback_data="menu_main")
        ]
    ])
    
    await message.answer(settings_text, reply_markup=keyboard, parse_mode="HTML")